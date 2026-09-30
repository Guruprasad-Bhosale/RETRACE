"""Unit tests for EvaluationAdapter."""

from uuid import uuid4

from apps.worker.evaluation.adapter import EvaluationAdapter
from apps.worker.evaluation.models import EndToEndStatus
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
from apps.worker.synthesis.models import (
    GeneratedTest,
    SynthesisStatus,
    TestFramework,
    TestLanguage,
    TestProvenance,
    ValidationStatus,
)
from benchmarks.models import (
    BenchmarkCase,
    BenchmarkCategory,
    BenchmarkInput,
    BenchmarkOracle,
    ExpectedOutcome,
    ExpectedSourceRegion,
)


def test_adapter_evaluates_complete_success():
    analysis_id = uuid4()
    case = BenchmarkCase(
        case_id="TEST-01",
        name="Test",
        description="Test",
        input_config=BenchmarkInput(
            version_a={"base_url": "http://a"},
            version_b={"base_url": "http://b"},
        ),
        oracle=BenchmarkOracle(
            expected_outcome=ExpectedOutcome.REGRESSION,
            expected_category=BenchmarkCategory.API_CONTRACT,
            expected_reproducible=True,
            expected_source_regions=[ExpectedSourceRegion(file_path="app.py", symbol_name="apply_coupon")],
            expected_commits=["8f31c2a"],
            expected_test_synthesized=True,
        ),
    )

    inv = InvestigationResult(
        investigation_id="inv-01",
        analysis_id=analysis_id,
        regression_id="reg-01",
        status=InvestigationStatus.COMPLETED,
        provenance=InvestigationProvenance(analysis_id=analysis_id, classification_id="reg-01", difference_id="diff-01"),
        classification=RegressionClassification(
            classification_id="reg-01",
            difference_id="diff-01",
            status=ClassificationStatus.REGRESSION_CANDIDATE,
            category=RegressionCategory.API_CONTRACT,
            rule_id="RULE-API",
            reason="Schema changed",
            evidence=ClassificationEvidence(difference_id="diff-01"),
        ),
        reproduction=ReproductionResult(
            reproduction_id="rep-01",
            classification_id="reg-01",
            difference_id="diff-01",
            rule_id="RULE-API",
            category="API_CONTRACT",
            status=ReproductionStatus.REPRODUCED,
            strategy=ReproductionStrategy.DIRECT_REPLAY,
            path=ReproductionPath(
                path_id="p-01",
                trajectory_id=uuid4(),
                classification_id="reg-01",
                difference_id="diff-01",
                seed_url="http://a",
                path_signature="sig-01",
            ),
        ),
        root_cause=RootCauseResult(
            root_cause_id="rc-01",
            classification_id="reg-01",
            difference_id="diff-01",
            category="API_CONTRACT",
            status=RootCauseStatus.LOCATED,
            primary_attribution=RootCauseAttribution(
                attribution_id="attr-01",
                source_location=SourceLocation(file_path="src/app.py", start_line=10, end_line=20, symbol_name="apply_coupon"),
                relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
                commit=CommitMetadata(commit_hash="8f31c2a", author_name="Dev", message="Fix coupon"),
                commit_attribution_type=CommitAttributionType.CAUSAL_COMMIT,
                diff_hunk=DiffHunk(old_start=10, old_lines=5, new_start=10, new_lines=6, header="@@"),
                explanation="Field renamed",
            ),
            provenance=RootCauseProvenance(classification_id="reg-01", difference_id="diff-01"),
        ),
        generated_test=GeneratedTest(
            test_id="t-01",
            regression_id="reg-01",
            framework=TestFramework.PLAYWRIGHT,
            language=TestLanguage.TYPESCRIPT,
            title="test_api_contract",
            description="Tests coupon validation",
            generated_source="test('schema', async ({ page }) => { expect(1).toBe(1); });",
            provenance=TestProvenance(classification_id="reg-01", difference_id="diff-01"),
            status=SynthesisStatus.SYNTHESIZED,
            validation_status=ValidationStatus.STRUCTURALLY_VALIDATED,
        ),
        report=EvidenceReport(
            report_id="rep-01",
            regression_id="reg-01",
            title="Report",
            status=ReportStatus.COMPLETE,
            summary="Summary",
            markdown_content="# Report",
            json_content={},
            evidence_chain=EvidenceChain(chain_id="c-01", nodes=[]),
            provenance=ReportProvenance(classification_id="reg-01", difference_id="diff-01"),
        ),
    )

    eval_res = EvaluationAdapter.evaluate_case(case, inv, analysis_id=analysis_id)

    assert eval_res.end_to_end_status == EndToEndStatus.COMPLETE_SUCCESS
    assert eval_res.detection.true_positive is True
    assert eval_res.classification.category_matched is True
    assert eval_res.reproduction.reproduction_matched is True
    assert eval_res.root_cause.file_matched is True
    assert eval_res.synthesis.test_generated is True
    assert len(eval_res.failure_taxonomy) == 0
