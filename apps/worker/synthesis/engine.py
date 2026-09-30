"""Test Synthesis Engine.

Primary entrypoint for synthesizing deterministic Playwright TypeScript regression
tests from Phase 7 classifications, Phase 8 reproductions, and Phase 9 root causes.
"""

from uuid import UUID

from apps.worker.regression.models import ClassificationStatus, RegressionClassification
from apps.worker.reproduction.models import (
    ReproductionResult,
    ReproductionStatus,
    ReproductionSuiteResult,
)
from apps.worker.rootcause.models import RootCauseResult, RootCauseSuiteResult
from apps.worker.synthesis.assertions import AssertionGenerator
from apps.worker.synthesis.config import SynthesisConfig
from apps.worker.synthesis.models import (
    GeneratedTest,
    SynthesisStatus,
    SynthesisSuiteResult,
    SynthesisSummary,
    TestProvenance,
    TestStep,
    ValidationStatus,
    compute_deterministic_test_id,
)
from apps.worker.synthesis.playwright import PlaywrightTypeScriptSerializer
from apps.worker.synthesis.selectors import DeterministicSelectorResolver
from apps.worker.synthesis.validator import GeneratedTestValidator


class TestSynthesisEngine:
    """Orchestrates deterministic regression test synthesis, serialization, and validation."""

    __test__ = False

    def __init__(self, config: SynthesisConfig | None = None) -> None:
        self.config = config or SynthesisConfig()
        self.selector_resolver = DeterministicSelectorResolver()
        self.assertion_generator = AssertionGenerator(config=self.config)
        self.serializer = PlaywrightTypeScriptSerializer(config=self.config)
        self.validator = GeneratedTestValidator()

    def synthesize_test(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None = None,
        root_cause: RootCauseResult | None = None,
    ) -> GeneratedTest:
        """Synthesize an executable Playwright regression test for a single regression."""
        # Check for non-regression
        if classification.status == ClassificationStatus.NON_REGRESSION:
            prov = TestProvenance(
                classification_id=classification.classification_id,
                difference_id=classification.difference_id,
                reproduction_id=reproduction.reproduction_id if reproduction else None,
                root_cause_id=root_cause.root_cause_id if root_cause else None,
            )
            return GeneratedTest(
                test_id=f"test_non_reg_{classification.classification_id[:8]}",
                regression_id=classification.classification_id,
                reproduction_id=reproduction.reproduction_id if reproduction else None,
                root_cause_id=root_cause.root_cause_id if root_cause else None,
                framework=self.config.framework,
                language=self.config.language,
                title=f"Non-Regression: {classification.category.value}",
                description="Classification is NON_REGRESSION; test generation skipped.",
                steps=[],
                assertions=[],
                provenance=prov,
                status=SynthesisStatus.INCOMPLETE,
                validation_status=ValidationStatus.NOT_VALIDATED,
                generated_source="// Non-regression: no regression test generated.",
                validation_notes=["Skipped test generation for non-regressive change."],
            )

        # 1. Resolve steps from reproduction path
        test_steps: list[TestStep] = []
        step_signatures: list[str] = []

        if reproduction and reproduction.path and reproduction.path.steps:
            for step in reproduction.path.steps:
                locator, strategy, desc = self.selector_resolver.resolve_step_locator(step)
                test_step = TestStep(
                    step_index=step.step_index,
                    action_type=step.action_type,
                    raw_target=step.raw_target or step.stable_target_identity,
                    resolved_selector=locator,
                    selector_strategy=strategy,
                    value=step.value,
                    timeout_ms=step.timeout_ms,
                    description=desc,
                    source_step_index=step.step_index,
                    causal_context={"target_strategy": step.target_strategy},
                )
                test_steps.append(test_step)
                step_signatures.append(f"{step.action_type.value}:{locator}:{step.value or ''}")

        # 2. Derive assertions from evidence
        assertions = self.assertion_generator.generate_assertions(
            classification=classification,
            reproduction=reproduction,
            root_cause=root_cause,
        )

        # 3. Assemble provenance
        source_locs: list[str] = []
        commit_hashes: list[str] = []
        if root_cause:
            if root_cause.primary_attribution:
                loc = root_cause.primary_attribution.source_location
                source_locs.append(f"{loc.file_path}:{loc.start_line}-{loc.end_line}")
                if root_cause.primary_attribution.commit:
                    commit_hashes.append(root_cause.primary_attribution.commit.commit_hash[:8])
            for attr in root_cause.attributions:
                l_str = f"{attr.source_location.file_path}:{attr.source_location.start_line}"
                if l_str not in source_locs:
                    source_locs.append(l_str)

        observation_ids: list[UUID] = []
        if reproduction and reproduction.path:
            observation_ids.extend(reproduction.path.observation_ids)

        provenance = TestProvenance(
            classification_id=classification.classification_id,
            difference_id=classification.difference_id,
            reproduction_id=reproduction.reproduction_id if reproduction else None,
            root_cause_id=root_cause.root_cause_id if root_cause else None,
            trajectory_id=reproduction.path.trajectory_id if reproduction and reproduction.path else None,
            observation_ids=observation_ids,
            artifact_references=classification.evidence.artifact_references if classification.evidence else [],
            source_locations=source_locs,
            commit_hashes=commit_hashes,
        )

        # 4. Compute deterministic test ID
        test_id = compute_deterministic_test_id(
            classification_id=classification.classification_id,
            reproduction_id=reproduction.reproduction_id if reproduction else None,
            framework=self.config.framework,
            language=self.config.language,
            step_signatures=step_signatures,
        )

        category_val = classification.category.value if hasattr(classification.category, "value") else str(classification.category)
        title = f"Regression Test: {category_val} [{classification.classification_id[:8]}]"
        desc = f"Reproduces {category_val} regression discovered by rule {classification.rule_id}."

        # 5. Determine synthesis status
        if not reproduction or reproduction.status != ReproductionStatus.REPRODUCED:
            status = SynthesisStatus.PARTIALLY_SYNTHESIZED if test_steps else SynthesisStatus.INCOMPLETE
        else:
            status = SynthesisStatus.SYNTHESIZED

        # 6. Create preliminary test model
        prelim_test = GeneratedTest(
            test_id=test_id,
            regression_id=classification.classification_id,
            reproduction_id=reproduction.reproduction_id if reproduction else None,
            root_cause_id=root_cause.root_cause_id if root_cause else None,
            framework=self.config.framework,
            language=self.config.language,
            target_version="A_B_DUAL" if self.config.include_ab_dual_mode else "STANDALONE",
            title=title,
            description=desc,
            steps=test_steps,
            assertions=assertions,
            provenance=provenance,
            status=status,
            validation_status=ValidationStatus.NOT_VALIDATED,
            generated_source="",
        )

        # 7. Serialize source code
        source_code = self.serializer.serialize(prelim_test)

        # 8. Validate test artifact
        val_test = prelim_test.model_copy(update={"generated_source": source_code})
        val_status, val_notes = self.validator.validate(val_test)

        return val_test.model_copy(
            update={
                "validation_status": val_status,
                "validation_notes": val_notes,
            }
        )

    def synthesize_suite(
        self,
        classifications: list[RegressionClassification],
        run_a_id: UUID,
        run_b_id: UUID,
        reproduction_suite: ReproductionSuiteResult | None = None,
        root_cause_suite: RootCauseSuiteResult | None = None,
    ) -> SynthesisSuiteResult:
        """Synthesize test suite for all given classifications."""
        repro_map: dict[str, ReproductionResult] = {}
        if reproduction_suite:
            for rep in reproduction_suite.results:
                repro_map[rep.classification_id] = rep

        rc_map: dict[str, RootCauseResult] = {}
        if root_cause_suite:
            for rc in root_cause_suite.results:
                rc_map[rc.classification_id] = rc

        # Sort classifications deterministically
        sorted_classifications = sorted(classifications, key=lambda c: c.deterministic_sort_key())

        tests: list[GeneratedTest] = []
        summary = SynthesisSummary(total_regressions_analyzed=len(sorted_classifications))

        for clf in sorted_classifications:
            rep = repro_map.get(clf.classification_id)
            rc = rc_map.get(clf.classification_id)

            gen_test = self.synthesize_test(
                classification=clf,
                reproduction=rep,
                root_cause=rc,
            )
            tests.append(gen_test)

            if gen_test.status == SynthesisStatus.SYNTHESIZED:
                summary.synthesized_count += 1
            elif gen_test.status == SynthesisStatus.PARTIALLY_SYNTHESIZED:
                summary.partially_synthesized_count += 1
            elif gen_test.status == SynthesisStatus.INCOMPLETE:
                summary.incomplete_count += 1
            elif gen_test.status == SynthesisStatus.UNSUPPORTED:
                summary.unsupported_count += 1

            if gen_test.validation_status == ValidationStatus.STRUCTURALLY_VALIDATED:
                summary.structurally_validated_count += 1
            elif gen_test.validation_status == ValidationStatus.VALIDATED:
                summary.runtime_validated_count += 1

        return SynthesisSuiteResult(
            run_a_id=run_a_id,
            run_b_id=run_b_id,
            tests=tests,
            summary=summary,
        )
