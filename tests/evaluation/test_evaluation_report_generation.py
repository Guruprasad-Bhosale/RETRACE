"""Unit tests for EvaluationReportGenerator."""

import json
from uuid import uuid4

from apps.worker.evaluation.models import (
    ClassificationEvaluation,
    DetectionEvaluation,
    EndToEndStatus,
    EvaluationResult,
    EvaluationSuiteResult,
    EvaluationSummaryMetrics,
    ReproductionEvaluation,
    ResourceMetrics,
    RootCauseEvaluation,
    SynthesisEvaluation,
    TimingMetrics,
)
from apps.worker.evaluation.reporter import EvaluationReportGenerator


def test_markdown_and_json_report_generation():
    result = EvaluationResult(
        case_id="DEF-001",
        workflow_id="wf-01",
        analysis_id=uuid4(),
        end_to_end_status=EndToEndStatus.COMPLETE_SUCCESS,
        detection=DetectionEvaluation(is_regression_expected=True, is_regression_detected=True, true_positive=True),
        classification=ClassificationEvaluation(expected_category="API_CONTRACT", observed_category="API_CONTRACT", category_matched=True),
        reproduction=ReproductionEvaluation(expected_reproduced=True, actual_reproduced=True, reproduction_matched=True),
        root_cause=RootCauseEvaluation(file_matched=True),
        synthesis=SynthesisEvaluation(expected_synthesized=True, test_generated=True, structurally_validated=True),
        timing=TimingMetrics(total_duration_s=12.5),
        resources=ResourceMetrics(),
    )

    summary = EvaluationSummaryMetrics(
        total_cases=1,
        complete_success_count=1,
        detection_tp=1,
        detection_precision=1.0,
        detection_recall=1.0,
        detection_specificity=1.0,
        classification_accuracy=1.0,
        reproduction_accuracy=1.0,
        file_localization_accuracy=1.0,
        test_generation_rate=1.0,
        test_structural_validity_rate=1.0,
        determinism_rate=1.0,
        confusion_matrix={"API_CONTRACT": {"API_CONTRACT": 1}},
    )

    suite_res = EvaluationSuiteResult(
        suite_id="test-suite",
        suite_name="Test Evaluation Suite",
        results=[result],
        summary=summary,
    )

    md = EvaluationReportGenerator.generate_markdown_report(suite_res)
    assert "# RETRACE Benchmark Evaluation Report" in md
    assert "DEF-001" in md
    assert "API_CONTRACT" in md
    assert "Confusion Matrix" in md

    json_str = EvaluationReportGenerator.generate_json_report(suite_res)
    parsed = json.loads(json_str)
    assert parsed["suite_id"] == "test-suite"
    assert len(parsed["results"]) == 1
