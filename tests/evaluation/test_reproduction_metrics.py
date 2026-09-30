"""Unit tests for reproduction metrics evaluation."""

from uuid import uuid4

from apps.worker.evaluation.adapter import EvaluationAdapter
from apps.worker.investigation.models import (
    InvestigationProvenance,
    InvestigationResult,
    InvestigationStatus,
)
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
    ReportStatus,
)
from apps.worker.reproduction.models import (
    MatchStatus,
    ReproductionPath,
    ReproductionResult,
    ReproductionStatus,
    ReproductionStrategy,
    ReproductionVerification,
)
from apps.worker.rootcause.models import (
    RootCauseProvenance,
    RootCauseResult,
    RootCauseStatus,
)
from benchmarks.models import (
    BenchmarkCase,
    BenchmarkCategory,
    BenchmarkInput,
    BenchmarkOracle,
    ExpectedOutcome,
)


def test_reproduction_matched_evaluation():
    case = BenchmarkCase(
        case_id="REPRO-01",
        name="Repro Case",
        description="Repro Case",
        input_config=BenchmarkInput(version_a={"base_url": "http://a"}, version_b={"base_url": "http://b"}),
        oracle=BenchmarkOracle(
            expected_outcome=ExpectedOutcome.REGRESSION,
            expected_category=BenchmarkCategory.FUNCTIONAL,
            expected_reproducible=True,
        ),
    )

    analysis_id = uuid4()
    inv = InvestigationResult(
        investigation_id="inv-r-1",
        analysis_id=analysis_id,
        regression_id="reg-r-1",
        status=InvestigationStatus.COMPLETED,
        provenance=InvestigationProvenance(analysis_id=analysis_id, classification_id="reg-r-1", difference_id="diff-1"),
        classification=RegressionClassification(
            classification_id="reg-r-1",
            difference_id="diff-1",
            status=ClassificationStatus.REGRESSION_CANDIDATE,
            category=RegressionCategory.FUNCTIONAL,
            rule_id="RULE-1",
            reason="Reason",
            evidence=ClassificationEvidence(difference_id="diff-1"),
        ),
        reproduction=ReproductionResult(
            reproduction_id="rep-1",
            classification_id="reg-r-1",
            difference_id="diff-1",
            rule_id="RULE-1",
            category="FUNCTIONAL",
            status=ReproductionStatus.REPRODUCED,
            strategy=ReproductionStrategy.DIRECT_REPLAY,
            path=ReproductionPath(
                path_id="p-1",
                trajectory_id=uuid4(),
                classification_id="reg-r-1",
                difference_id="diff-1",
                seed_url="http://a",
                path_signature="sig-1",
            ),
            final_verification=ReproductionVerification(
                expected_difference_id="diff-1",
                expected_classification_id="reg-r-1",
                expected_rule_id="RULE-1",
                expected_category="FUNCTIONAL",
                match_status=MatchStatus.FULL_MATCH,
                observed_match=True,
            ),
        ),
        root_cause=RootCauseResult(
            root_cause_id="rc-1",
            classification_id="reg-r-1",
            difference_id="diff-1",
            category="FUNCTIONAL",
            status=RootCauseStatus.LOCATED,
            provenance=RootCauseProvenance(classification_id="reg-r-1", difference_id="diff-1"),
        ),
        report=EvidenceReport(
            report_id="rep-1",
            regression_id="reg-r-1",
            title="Rep",
            status=ReportStatus.COMPLETE,
            summary="Sum",
            markdown_content="# Rep",
            json_content={},
            evidence_chain=EvidenceChain(chain_id="c-1", nodes=[]),
            provenance=ReportProvenance(classification_id="reg-r-1", difference_id="diff-1"),
        ),
    )

    eval_res = EvaluationAdapter.evaluate_case(case, inv, analysis_id=analysis_id)
    assert eval_res.reproduction.actual_reproduced is True
    assert eval_res.reproduction.reproduction_matched is True
    assert eval_res.reproduction.match_status == MatchStatus.FULL_MATCH.value
