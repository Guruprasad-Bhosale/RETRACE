"""RETRACE Evaluation Adapter.

Authoritative bridge that compares an InvestigationResult (or workflow state)
against a BenchmarkOracle to produce an EvaluationResult.

CRITICAL ARCHITECTURAL CONTRACT:
This adapter is the ONLY component permitted to inspect the BenchmarkOracle.
"""

from typing import Any
from uuid import UUID, uuid4

from apps.worker.evaluation.metrics import evaluate_detection
from apps.worker.evaluation.models import (
    ClassificationEvaluation,
    EndToEndStatus,
    EvaluationResult,
    FailureTaxonomy,
    ReproductionEvaluation,
    ResourceMetrics,
    RootCauseEvaluation,
    SynthesisEvaluation,
    TimingMetrics,
)
from apps.worker.investigation.models import InvestigationResult, InvestigationSuiteResult
from benchmarks.models import BenchmarkCase, BenchmarkOracle, ExpectedOutcome


class EvaluationAdapter:
    """Compares RETRACE investigation outputs against benchmark ground-truth oracles."""

    @staticmethod
    def evaluate_case(
        case: BenchmarkCase,
        investigation_output: InvestigationResult | InvestigationSuiteResult | dict[str, Any] | None,
        workflow_id: str = "eval-wf",
        analysis_id: UUID | None = None,
        phase_timings: dict[str, float] | None = None,
        resource_stats: dict[str, int] | None = None,
    ) -> EvaluationResult:
        """Evaluate a single benchmark case output against its private oracle."""
        oracle: BenchmarkOracle = case.oracle
        effective_analysis_id = analysis_id or uuid4()
        failures: list[FailureTaxonomy] = []
        notes: list[str] = []

        # ----------------------------------------------------------------------
        # 1. Extract authoritative investigation result
        # ----------------------------------------------------------------------
        inv_result: InvestigationResult | None = None
        if isinstance(investigation_output, InvestigationResult):
            inv_result = investigation_output
        elif isinstance(investigation_output, InvestigationSuiteResult):
            if investigation_output.investigations:
                inv_result = investigation_output.investigations[0]
        elif isinstance(investigation_output, dict):
            # Check if an InvestigationSuiteResult is stored in state dict
            suite = investigation_output.get("investigation_suite")
            if isinstance(suite, InvestigationSuiteResult) and suite.investigations:
                inv_result = suite.investigations[0]
            elif isinstance(suite, dict) and suite.get("investigations"):
                # Handle raw dict serialization
                pass

        # ----------------------------------------------------------------------
        # 2. Detection Evaluation
        # ----------------------------------------------------------------------
        has_detected_regression = inv_result is not None and inv_result.status.value in ("COMPLETED", "INCONCLUSIVE")
        if (
            isinstance(investigation_output, dict)
            and investigation_output.get("classification_result") is not None
        ):
            clf_res = investigation_output["classification_result"]
            if hasattr(clf_res, "classifications"):
                has_detected_regression = any(
                    c.status.value == "REGRESSION_CANDIDATE" for c in clf_res.classifications
                )

        detection_eval = evaluate_detection(oracle.expected_outcome, has_detected_regression)

        if detection_eval.false_positive:
            failures.append(FailureTaxonomy.CLASSIFICATION_FAILURE)
            notes.append("False positive: Non-regression flagged as regression candidate.")
        elif detection_eval.false_negative:
            failures.append(FailureTaxonomy.CLASSIFICATION_FAILURE)
            notes.append("False negative: Expected regression was not detected.")

        # ----------------------------------------------------------------------
        # 3. Classification Evaluation
        # ----------------------------------------------------------------------
        observed_category: str | None = None
        observed_severity: str | None = None
        cat_matched = False
        sev_matched = False

        if inv_result and inv_result.classification:
            observed_category = inv_result.classification.category.value.upper()
            observed_severity = getattr(inv_result.classification, "severity", "MEDIUM")

        if observed_category:
            cat_matched = (
                observed_category == oracle.expected_category.value.upper()
                or (
                    oracle.expected_outcome == ExpectedOutcome.NON_REGRESSION
                    and observed_category == "NON_REGRESSION"
                )
            )
        elif oracle.expected_outcome == ExpectedOutcome.NON_REGRESSION:
            # If no regression was classified for a non-regression case, classification succeeds
            observed_category = "NON_REGRESSION"
            cat_matched = True

        if not cat_matched and oracle.expected_outcome == ExpectedOutcome.REGRESSION:
            failures.append(FailureTaxonomy.CLASSIFICATION_FAILURE)
            notes.append(f"Classification category mismatch: expected {oracle.expected_category.value}, observed {observed_category}")

        classification_eval = ClassificationEvaluation(
            expected_category=oracle.expected_category.value,
            observed_category=observed_category,
            category_matched=cat_matched,
            expected_severity=oracle.expected_severity,
            observed_severity=observed_severity,
            severity_matched=sev_matched,
        )

        # ----------------------------------------------------------------------
        # 4. Reproduction Evaluation
        # ----------------------------------------------------------------------
        actual_reproduced = False
        match_status_str: str | None = None
        repro_matched = False
        repro_rate = 0.0
        attempts_count = 0

        if inv_result and inv_result.reproduction:
            repro = inv_result.reproduction
            actual_reproduced = repro.status.value in ("REPRODUCED", "CONFIRMED")
            repro_rate = getattr(repro, "reproduction_rate", 1.0 if actual_reproduced else 0.0)
            attempts_count = len(repro.attempts) if hasattr(repro, "attempts") else 1
            if hasattr(repro, "final_verification") and repro.final_verification:
                match_status_str = getattr(repro.final_verification, "match_status", None)

        if oracle.expected_outcome == ExpectedOutcome.NON_REGRESSION:
            # Non-regressions are not expected to be reproduced
            repro_matched = not actual_reproduced
        elif oracle.expected_outcome == ExpectedOutcome.INCONCLUSIVE:
            # Inconclusive cases expect reproduction failure or NO_MATCH
            repro_matched = not actual_reproduced
        else:
            repro_matched = (actual_reproduced == oracle.expected_reproducible)

        if not repro_matched and oracle.expected_outcome == ExpectedOutcome.REGRESSION:
            failures.append(FailureTaxonomy.REPRODUCTION_FAILURE)
            notes.append("Reproduction mismatch: expected reproducible regression, but reproduction failed.")

        reproduction_eval = ReproductionEvaluation(
            expected_reproduced=oracle.expected_reproducible,
            actual_reproduced=actual_reproduced,
            match_status=match_status_str,
            reproduction_matched=repro_matched,
            reproduction_rate=repro_rate,
            attempts_count=attempts_count,
        )

        # ----------------------------------------------------------------------
        # 5. Root Cause Evaluation
        # ----------------------------------------------------------------------
        file_matched = False
        symbol_matched = False
        line_region_matched = False
        commit_matched = False
        observed_files: list[str] = []
        observed_commits: list[str] = []
        attribution_tier_str: str | None = None
        loc_status_str: str | None = None

        if inv_result and inv_result.root_cause:
            rc = inv_result.root_cause
            loc_status_str = rc.status.value
            if hasattr(rc, "primary_attribution") and rc.primary_attribution:
                primary = rc.primary_attribution
                if hasattr(primary, "relationship_type") and primary.relationship_type:
                    attribution_tier_str = primary.relationship_type.value
                elif hasattr(primary, "commit_attribution_type") and primary.commit_attribution_type:
                    attribution_tier_str = primary.commit_attribution_type.value

                src_loc = getattr(primary, "source_location", None) or getattr(primary, "location", None)
                if src_loc:
                    observed_files.append(src_loc.file_path)
                    # Check symbol
                    if src_loc.symbol_name:
                        for exp_loc in oracle.expected_source_regions:
                            if exp_loc.symbol_name and exp_loc.symbol_name in src_loc.symbol_name:
                                symbol_matched = True

                if getattr(primary, "commit", None):
                    observed_commits.append(primary.commit.commit_hash)

            # Check candidate locations
            if hasattr(rc, "candidate_locations"):
                for loc in rc.candidate_locations:
                    if loc.file_path not in observed_files:
                        observed_files.append(loc.file_path)

        # Evaluate file matching (normalized path check)
        exp_file_basenames = [
            f.file_path.replace("\\", "/").split("/")[-1]
            for f in oracle.expected_source_regions
        ]
        for obs_f in observed_files:
            obs_base = obs_f.replace("\\", "/").split("/")[-1]
            if obs_base in exp_file_basenames:
                file_matched = True
                break

        # Evaluate commit matching
        for obs_c in observed_commits:
            for exp_c in oracle.expected_commits:
                if exp_c in obs_c or obs_c in exp_c:
                    commit_matched = True
                    break

        if oracle.expected_outcome == ExpectedOutcome.NON_REGRESSION:
            file_matched = True
            commit_matched = True
        elif oracle.expected_source_regions and not file_matched:
            failures.append(FailureTaxonomy.ROOT_CAUSE_FAILURE)
            notes.append(f"Root cause file mismatch: expected {exp_file_basenames}, observed {observed_files}")

        root_cause_eval = RootCauseEvaluation(
            file_matched=file_matched,
            symbol_matched=symbol_matched,
            line_region_matched=line_region_matched,
            commit_matched=commit_matched,
            expected_files=[f.file_path for f in oracle.expected_source_regions],
            observed_files=observed_files,
            expected_commits=oracle.expected_commits,
            observed_commits=observed_commits,
            attribution_tier=attribution_tier_str,
            localization_status=loc_status_str,
        )

        # ----------------------------------------------------------------------
        # 6. Test Synthesis Evaluation
        # ----------------------------------------------------------------------
        test_gen = False
        struct_valid = False
        code_size = 0
        assertions = 0

        if inv_result and inv_result.generated_test:
            test_art = inv_result.generated_test
            test_gen = True
            code_content = test_art.generated_source or ""
            code_size = len(code_content.encode("utf-8"))
            assertions = len(test_art.assertions)

            # Structural validation: verify syntax keywords and non-empty assertions
            if (
                ("test(" in code_content or "def test_" in code_content or "expect(" in code_content or "assert" in code_content)
                and test_art.framework
            ):
                struct_valid = True

        if oracle.expected_outcome == ExpectedOutcome.NON_REGRESSION:
            test_eval_matched = (not test_gen)
        else:
            test_eval_matched = (test_gen == oracle.expected_test_synthesized)

        if not test_eval_matched and oracle.expected_outcome == ExpectedOutcome.REGRESSION:
            failures.append(FailureTaxonomy.SYNTHESIS_FAILURE)
            notes.append("Test synthesis missing: expected generated regression test.")

        synthesis_eval = SynthesisEvaluation(
            expected_synthesized=oracle.expected_test_synthesized,
            test_generated=test_gen,
            structurally_validated=struct_valid,
            executed_successfully=struct_valid,
            reproduces_target=actual_reproduced,
            code_size_bytes=code_size,
            assertions_count=assertions,
        )

        # ----------------------------------------------------------------------
        # 7. End-to-End Status Determination
        # ----------------------------------------------------------------------
        if oracle.expected_outcome == ExpectedOutcome.NON_REGRESSION:
            if detection_eval.true_negative and cat_matched:
                e2e_status = EndToEndStatus.COMPLETE_SUCCESS
            else:
                e2e_status = EndToEndStatus.FAILURE
        elif oracle.expected_outcome == ExpectedOutcome.INCONCLUSIVE:
            if repro_matched:
                e2e_status = EndToEndStatus.COMPLETE_SUCCESS
            else:
                e2e_status = EndToEndStatus.INCONCLUSIVE
        else:
            # Standard Regression Case
            if (
                detection_eval.true_positive
                and cat_matched
                and repro_matched
                and file_matched
            ):
                e2e_status = EndToEndStatus.COMPLETE_SUCCESS
            elif detection_eval.true_positive and (cat_matched or repro_matched):
                e2e_status = EndToEndStatus.PARTIAL_SUCCESS
            elif detection_eval.false_negative:
                e2e_status = EndToEndStatus.FAILURE
            else:
                e2e_status = EndToEndStatus.FAILURE

        # Deterministic Signature (excludes non-deterministic timestamps)
        sig_raw = (
            f"{case.case_id}:{e2e_status.value}:{observed_category}:{actual_reproduced}:"
            f"{file_matched}:{test_gen}"
        )

        return EvaluationResult(
            case_id=case.case_id,
            workflow_id=workflow_id,
            analysis_id=effective_analysis_id,
            end_to_end_status=e2e_status,
            detection=detection_eval,
            classification=classification_eval,
            reproduction=reproduction_eval,
            root_cause=root_cause_eval,
            synthesis=synthesis_eval,
            timing=TimingMetrics(
                total_duration_s=sum((phase_timings or {}).values()),
                phase_durations_s=phase_timings or {},
            ),
            resources=ResourceMetrics(
                browser_sessions_count=(resource_stats or {}).get("browser_sessions", 2),
                artifacts_bytes=(resource_stats or {}).get("artifact_bytes", 0),
                workflow_retries=(resource_stats or {}).get("retries", 0),
                nodes_executed=(resource_stats or {}).get("nodes_executed", 10),
            ),
            failure_taxonomy=failures,
            deterministic_signature=sig_raw,
            notes=notes,
        )
