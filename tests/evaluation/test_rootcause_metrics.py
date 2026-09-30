"""Unit tests for root cause and commit attribution metrics."""

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
    ReproductionPath,
    ReproductionResult,
    ReproductionStatus,
    ReproductionStrategy,
)
from apps.worker.rootcause.models import (
    AttributionRelationshipType,
    CommitAttributionType,
    CommitMetadata,
    DiffHunk,
    RootCauseAttribution,
    RootCauseProvenance,
    RootCauseResult,
    RootCauseStatus,
    SourceLocation,
)
from benchmarks.models import (
    BenchmarkCase,
    BenchmarkCategory,
    BenchmarkInput,
    BenchmarkOracle,
    ExpectedOutcome,
    ExpectedSourceRegion,
)


def test_root_cause_file_and_commit_evaluation():
    case = BenchmarkCase(
        case_id="RC-01",
        name="Root Cause Case",
        description="Root Cause Case",
        input_config=BenchmarkInput(version_a={"base_url": "http://a"}, version_b={"base_url": "http://b"}),
        oracle=BenchmarkOracle(
            expected_outcome=ExpectedOutcome.REGRESSION,
            expected_category=BenchmarkCategory.API_CONTRACT,
            expected_source_regions=[
                ExpectedSourceRegion(file_path="app.py", symbol_name="apply_coupon")
            ],
            expected_commits=["8f31c2a"],
        ),
    )

    analysis_id = uuid4()
    inv = InvestigationResult(
        investigation_id="inv-rc-1",
        analysis_id=analysis_id,
        regression_id="reg-rc-1",
        status=InvestigationStatus.COMPLETED,
        provenance=InvestigationProvenance(analysis_id=analysis_id, classification_id="reg-rc-1", difference_id="diff-1"),
        classification=RegressionClassification(
            classification_id="reg-rc-1",
            difference_id="diff-1",
            status=ClassificationStatus.REGRESSION_CANDIDATE,
            category=RegressionCategory.API_CONTRACT,
            rule_id="RULE-1",
            reason="Reason",
            evidence=ClassificationEvidence(difference_id="diff-1"),
        ),
        reproduction=ReproductionResult(
            reproduction_id="rep-1",
            classification_id="reg-rc-1",
            difference_id="diff-1",
            rule_id="RULE-1",
            category="API_CONTRACT",
            status=ReproductionStatus.REPRODUCED,
            strategy=ReproductionStrategy.DIRECT_REPLAY,
            path=ReproductionPath(
                path_id="p-1",
                trajectory_id=uuid4(),
                classification_id="reg-rc-1",
                difference_id="diff-1",
                seed_url="http://a",
                path_signature="sig-1",
            ),
        ),
        root_cause=RootCauseResult(
            root_cause_id="rc-1",
            classification_id="reg-rc-1",
            difference_id="diff-1",
            category="API_CONTRACT",
            status=RootCauseStatus.LOCATED,
            primary_attribution=RootCauseAttribution(
                attribution_id="attr-rc-1",
                source_location=SourceLocation(file_path="lab/applications/commerce/v2/app.py", start_line=10, end_line=20, symbol_name="apply_coupon"),
                relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
                commit=CommitMetadata(commit_hash="8f31c2a", author_name="Dev", message="Fix coupon"),
                commit_attribution_type=CommitAttributionType.CAUSAL_COMMIT,
                diff_hunk=DiffHunk(old_start=10, old_lines=5, new_start=10, new_lines=6, header="@@"),
                explanation="Field renamed",
            ),
            provenance=RootCauseProvenance(classification_id="reg-rc-1", difference_id="diff-1"),
        ),
        report=EvidenceReport(
            report_id="rep-1",
            regression_id="reg-rc-1",
            title="Rep",
            status=ReportStatus.COMPLETE,
            summary="Sum",
            markdown_content="# Rep",
            json_content={},
            evidence_chain=EvidenceChain(chain_id="c-1", nodes=[]),
            provenance=ReportProvenance(classification_id="reg-rc-1", difference_id="diff-1"),
        ),
    )

    eval_res = EvaluationAdapter.evaluate_case(case, inv, analysis_id=analysis_id)
    assert eval_res.root_cause.file_matched is True
    assert eval_res.root_cause.symbol_matched is True
    assert eval_res.root_cause.commit_matched is True
