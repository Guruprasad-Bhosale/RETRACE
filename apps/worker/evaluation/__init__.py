"""RETRACE Scientific Evaluation & Benchmark Package."""

from apps.worker.evaluation.adapter import EvaluationAdapter
from apps.worker.evaluation.baseline import EvaluationBaselineManager
from apps.worker.evaluation.metrics import (
    compute_category_metrics,
    compute_confusion_matrix,
    evaluate_detection,
    summarize_suite_metrics,
)
from apps.worker.evaluation.models import (
    CategoryMetricDetail,
    ClassificationEvaluation,
    DetectionEvaluation,
    EndToEndStatus,
    EvaluationResult,
    EvaluationSuiteResult,
    EvaluationSummaryMetrics,
    FailureTaxonomy,
    ReproductionEvaluation,
    RootCauseEvaluation,
    SynthesisEvaluation,
)
from apps.worker.evaluation.reporter import EvaluationReportGenerator
from apps.worker.evaluation.runner import BenchmarkRunner

__all__ = [
    "BenchmarkRunner",
    "CategoryMetricDetail",
    "ClassificationEvaluation",
    "DetectionEvaluation",
    "EndToEndStatus",
    "EvaluationAdapter",
    "EvaluationBaselineManager",
    "EvaluationReportGenerator",
    "EvaluationResult",
    "EvaluationSuiteResult",
    "EvaluationSummaryMetrics",
    "FailureTaxonomy",
    "ReproductionEvaluation",
    "RootCauseEvaluation",
    "SynthesisEvaluation",
    "compute_category_metrics",
    "compute_confusion_matrix",
    "evaluate_detection",
    "summarize_suite_metrics",
]
