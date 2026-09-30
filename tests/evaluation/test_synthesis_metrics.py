"""Unit tests for test synthesis metrics evaluation."""

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
    RootCauseProvenance,
    RootCauseResult,
    RootCauseStatus,
)
from apps.worker.synthesis.models import (
    AssertionCategory,
    GeneratedTest,
    SynthesisStatus,
    TestAssertion,
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
)


def test_test_synthesis_structural_validation():
    case = BenchmarkCase(
        case_id="SYNTH-01",
        name="Synth Case",
        description="Synth Case",
        input_config=BenchmarkInput(version_a={"base_url": "http://a"}, version_b={"base_url": "http://b"}),
        oracle=BenchmarkOracle(
            expected_outcome=ExpectedOutcome.REGRESSION,
            expected_category=BenchmarkCategory.FUNCTIONAL,
            expected_test_synthesized=True,
        ),
    )

    analysis_id = uuid4()
    inv = InvestigationResult(
        investigation_id="inv-s-1",
        analysis_id=analysis_id,
        regression_id="reg-s-1",
        status=InvestigationStatus.COMPLETED,
        provenance=InvestigationProvenance(analysis_id=analysis_id, classification_id="reg-s-1", difference_id="diff-1"),
        classification=RegressionClassification(
            classification_id="reg-s-1",
            difference_id="diff-1",
            status=ClassificationStatus.REGRESSION_CANDIDATE,
            category=RegressionCategory.FUNCTIONAL,
            rule_id="RULE-1",
            reason="Reason",
            evidence=ClassificationEvidence(difference_id="diff-1"),
        ),
        reproduction=ReproductionResult(
            reproduction_id="rep-1",
            classification_id="reg-s-1",
            difference_id="diff-1",
            rule_id="RULE-1",
            category="FUNCTIONAL",
            status=ReproductionStatus.REPRODUCED,
            strategy=ReproductionStrategy.DIRECT_REPLAY,
            path=ReproductionPath(
                path_id="p-1",
                trajectory_id=uuid4(),
                classification_id="reg-s-1",
                difference_id="diff-1",
                seed_url="http://a",
                path_signature="sig-1",
            ),
        ),
        root_cause=RootCauseResult(
            root_cause_id="rc-1",
            classification_id="reg-s-1",
            difference_id="diff-1",
            category="FUNCTIONAL",
            status=RootCauseStatus.LOCATED,
            provenance=RootCauseProvenance(classification_id="reg-s-1", difference_id="diff-1"),
        ),
        generated_test=GeneratedTest(
            test_id="t-01",
            regression_id="reg-s-1",
            framework=TestFramework.PLAYWRIGHT,
            language=TestLanguage.TYPESCRIPT,
            title="test_checkout_regression",
            description="Checkout regression",
            generated_source="import { test, expect } from '@playwright/test';\ntest('checkout', async ({ page }) => {\n  await expect(page.locator('#btn')).toBeVisible();\n});",
            assertions=[
                TestAssertion(
                    assertion_id="ast-1",
                    category=AssertionCategory.UI_STATE,
                    assertion_type="toBeVisible",
                    subject="locator('#btn')",
                    expected_value="visible",
                    evidence_id="diff-1",
                    reasoning="Button must be visible on checkout page",
                )
            ],
            provenance=TestProvenance(classification_id="reg-s-1", difference_id="diff-1"),
            status=SynthesisStatus.SYNTHESIZED,
            validation_status=ValidationStatus.STRUCTURALLY_VALIDATED,
        ),
        report=EvidenceReport(
            report_id="rep-1",
            regression_id="reg-s-1",
            title="Rep",
            status=ReportStatus.COMPLETE,
            summary="Sum",
            markdown_content="# Rep",
            json_content={},
            evidence_chain=EvidenceChain(chain_id="c-1", nodes=[]),
            provenance=ReportProvenance(classification_id="reg-s-1", difference_id="diff-1"),
        ),
    )

    eval_res = EvaluationAdapter.evaluate_case(case, inv, analysis_id=analysis_id)
    assert eval_res.synthesis.test_generated is True
    assert eval_res.synthesis.structurally_validated is True
    assert eval_res.synthesis.assertions_count == 1
    assert eval_res.synthesis.code_size_bytes > 0
