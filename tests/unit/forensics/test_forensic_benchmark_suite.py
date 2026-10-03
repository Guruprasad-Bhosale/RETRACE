"""Unit and Benchmark evaluation tests for Forensic Benchmark Cases A through J."""

import json
from pathlib import Path
from uuid import uuid4

from apps.worker.investigation.models import InvestigationProvenance, InvestigationResult
from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
)
from apps.worker.reporting.models import (
    EvidenceChain,
    EvidenceReport,
    ReportProvenance,
)
from apps.worker.reproduction.models import ReproductionResult, ReproductionStatus
from apps.worker.rootcause.models import (
    AttributionRelationshipType,
    CommitMetadata,
    RootCauseAttribution,
    RootCauseProvenance,
    RootCauseResult,
    RootCauseStatus,
    SourceLocation,
)
from apps.worker.synthesis.models import GeneratedTest
from packages.forensics.engine import ForensicIntelligenceEngine
from packages.forensics.evaluator import (
    BenchmarkCaseGroundTruth,
    ForensicBenchmarkEvaluator,
)


def _build_investigation_from_case(case_data: dict) -> InvestigationResult:
    """Build an InvestigationResult fixture from a benchmark case definition."""
    cat_map = {
        "CALCULATION_LOGIC": RegressionCategory.CALCULATION,
        "DOM_RENDER_LOGIC": RegressionCategory.UI_BEHAVIOR,
        "API_CONTRACT": RegressionCategory.API_CONTRACT,
        "TIMING_RACE_CONDITION": RegressionCategory.STATE,
        "STYLING_FORMATTING": RegressionCategory.UI_BEHAVIOR,
        "UNKNOWN": RegressionCategory.UNKNOWN,
    }
    cat = cat_map.get(case_data["category"], RegressionCategory.UNKNOWN)

    classification = RegressionClassification(
        classification_id=f"cls_{case_data['case_id']}",
        difference_id=f"diff_{case_data['case_id']}",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=cat,
        rule_id=f"RULE-{case_data['case_id']}",
        reason=case_data["reason"],
        evidence=ClassificationEvidence(
            difference_id=f"diff_{case_data['case_id']}",
            canonical_subject="page#content",
            details={"divergence": case_data["reason"]},
        ),
    )



    root_cause = None
    if case_data.get("has_source") and case_data.get("source_file"):
        loc = SourceLocation(
            file_path=case_data["source_file"],
            start_line=case_data["source_line"],
            end_line=case_data["source_line"] + 10,
            symbol_name="execute",
        )
        commit = (
            CommitMetadata(
                commit_hash=case_data["commit_hash"],
                author_name="dev",
                author_email="dev@example.com",
                message="Modify behavior",
            )
            if case_data.get("commit_hash")
            else None
        )
        attr = RootCauseAttribution(
            attribution_id=f"attr_{case_data['case_id']}",
            source_location=loc,
            commit=commit,
            relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
            explanation="Direct AST modification detected",
        )
        root_cause = RootCauseResult(
            root_cause_id=f"rc_{case_data['case_id']}",
            classification_id=f"cls_{case_data['case_id']}",
            difference_id=f"diff_{case_data['case_id']}",
            category=cat.value,
            status=RootCauseStatus.LOCATED,
            primary_attribution=attr,
            attributions=[attr],
            provenance=RootCauseProvenance(
                classification_id=f"cls_{case_data['case_id']}",
                difference_id=f"diff_{case_data['case_id']}",
            ),

        )


    reproduction = None
    repro_status = case_data.get("reproduction_status")
    if repro_status == "REPRODUCED":
        from apps.worker.reproduction.models import ReproductionPath, ReproductionStrategy
        reproduction = ReproductionResult(
            reproduction_id=f"rep_{case_data['case_id']}",
            classification_id=f"cls_{case_data['case_id']}",
            difference_id=f"diff_{case_data['case_id']}",
            rule_id="RULE-BENCHMARK",
            category="FUNCTIONAL",
            status=ReproductionStatus.REPRODUCED,
            strategy=ReproductionStrategy.DIRECT_REPLAY,
            path=ReproductionPath(
                path_id=f"path_{case_data['case_id']}",
                trajectory_id=uuid4(),
                classification_id=f"cls_{case_data['case_id']}",
                difference_id=f"diff_{case_data['case_id']}",
                seed_url="http://127.0.0.1:3000/",
                path_signature="step=0|type=NAVIGATE",
            ),
        )
    elif repro_status == "FAILED":
        from apps.worker.reproduction.models import ReproductionPath, ReproductionStrategy
        reproduction = ReproductionResult(
            reproduction_id=f"rep_{case_data['case_id']}",
            classification_id=f"cls_{case_data['case_id']}",
            difference_id=f"diff_{case_data['case_id']}",
            rule_id="RULE-BENCHMARK",
            category="FUNCTIONAL",
            status=ReproductionStatus.FAILED,
            strategy=ReproductionStrategy.DIRECT_REPLAY,
            path=ReproductionPath(
                path_id=f"path_{case_data['case_id']}",
                trajectory_id=uuid4(),
                classification_id=f"cls_{case_data['case_id']}",
                difference_id=f"diff_{case_data['case_id']}",
                seed_url="http://127.0.0.1:3000/",
                path_signature="step=0|type=NAVIGATE",
            ),
        )


    from apps.worker.reporting.models import ReportStatus
    from apps.worker.synthesis.models import TestProvenance

    ana_id = uuid4()
    cls_id = f"cls_{case_data['case_id']}"
    diff_id = f"diff_{case_data['case_id']}"

    return InvestigationResult(
        investigation_id=f"inv_{case_data['case_id'].lower()}",
        analysis_id=ana_id,
        regression_id=cls_id,
        classification=classification,
        reproduction=reproduction,
        root_cause=root_cause,
        generated_test=GeneratedTest(
            test_id=f"test_{case_data['case_id']}",
            regression_id=cls_id,
            title=f"Test {case_data['case_id']}",
            description="Playwright regression test",
            provenance=TestProvenance(classification_id=cls_id, difference_id=diff_id),
            generated_source="// Playwright test code",
        ),
        report=EvidenceReport(
            report_id=f"rep_{case_data['case_id']}",
            investigation_id=f"inv_{case_data['case_id'].lower()}",
            regression_id=cls_id,
            title=f"Report {case_data['case_id']}",
            status=ReportStatus.COMPLETE,
            summary="Summary",
            sections=[],
            evidence_chain=EvidenceChain(chain_id="chain_0", nodes=[]),
            markdown_content="# Report",
            provenance=ReportProvenance(classification_id=cls_id, difference_id=diff_id),
        ),
        status="COMPLETED",
        provenance=InvestigationProvenance(analysis_id=ana_id, classification_id=cls_id, difference_id=diff_id),
    )




def test_forensic_benchmark_dataset_all_cases():
    """Evaluate all 10 forensic benchmark cases A through J against ground truth."""
    fixtures_path = Path("tests/fixtures/forensics/forensic_cases.json")
    with open(fixtures_path, encoding="utf-8") as f:
        cases = json.load(f)

    assert len(cases) == 10

    results = []
    for case in cases:
        inv = _build_investigation_from_case(case)
        explanation = ForensicIntelligenceEngine.explain_investigation(inv)
        gt = BenchmarkCaseGroundTruth(**case["ground_truth"])
        res = ForensicBenchmarkEvaluator.evaluate(explanation, gt)
        results.append(res)
        assert res.passed is True, f"Benchmark case {case['case_id']} failed: {res.diagnostic_notes}"

    pass_count = sum(1 for r in results if r.passed)
    assert pass_count == 10
