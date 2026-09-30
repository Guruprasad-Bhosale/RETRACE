"""RETRACE Scientific Evaluation Domain Models & Metrics Schemas.

Provides strongly typed models for multi-subsystem benchmark evaluation,
failure taxonomy, detection/classification/reproduction/localization/synthesis
granular metrics, and evaluation suite reporting.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Return current UTC timestamp with timezone."""
    return datetime.now(UTC)


class FailureTaxonomy(StrEnum):
    """Categorized root failure domains for objective defect diagnosis."""

    INPUT_FAILURE = "INPUT_FAILURE"
    OBSERVATION_FAILURE = "OBSERVATION_FAILURE"
    EXPLORATION_FAILURE = "EXPLORATION_FAILURE"
    ALIGNMENT_FAILURE = "ALIGNMENT_FAILURE"
    DIFF_FAILURE = "DIFF_FAILURE"
    CLASSIFICATION_FAILURE = "CLASSIFICATION_FAILURE"
    REPRODUCTION_FAILURE = "REPRODUCTION_FAILURE"
    ROOT_CAUSE_FAILURE = "ROOT_CAUSE_FAILURE"
    SYNTHESIS_FAILURE = "SYNTHESIS_FAILURE"
    REPORT_FAILURE = "REPORT_FAILURE"
    ORCHESTRATION_FAILURE = "ORCHESTRATION_FAILURE"
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"


class EndToEndStatus(StrEnum):
    """Overall evaluation outcome for an individual benchmark case."""

    COMPLETE_SUCCESS = "COMPLETE_SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    INCONCLUSIVE = "INCONCLUSIVE"
    FAILURE = "FAILURE"


class DetectionEvaluation(BaseModel):
    """Evaluation of whether a regression was correctly detected vs missed."""

    model_config = ConfigDict(extra="forbid")

    is_regression_expected: bool
    is_regression_detected: bool
    true_positive: bool = False
    false_positive: bool = False
    false_negative: bool = False
    true_negative: bool = False


class ClassificationEvaluation(BaseModel):
    """Evaluation of semantic category and severity classification accuracy."""

    model_config = ConfigDict(extra="forbid")

    expected_category: str
    observed_category: str | None = None
    category_matched: bool = False
    expected_severity: str = "MEDIUM"
    observed_severity: str | None = None
    severity_matched: bool = False


class ReproductionEvaluation(BaseModel):
    """Evaluation of autonomous replay and regression reproduction accuracy."""

    model_config = ConfigDict(extra="forbid")

    expected_reproduced: bool
    actual_reproduced: bool
    match_status: str | None = None  # FULL_MATCH, PARTIAL_MATCH, NO_MATCH, etc.
    reproduction_matched: bool = False
    reproduction_rate: float = 0.0
    attempts_count: int = 0


class RootCauseEvaluation(BaseModel):
    """Evaluation of source code and commit localization accuracy."""

    model_config = ConfigDict(extra="forbid")

    file_matched: bool = False
    symbol_matched: bool = False
    line_region_matched: bool = False
    commit_matched: bool = False
    expected_files: list[str] = Field(default_factory=list)
    observed_files: list[str] = Field(default_factory=list)
    expected_commits: list[str] = Field(default_factory=list)
    observed_commits: list[str] = Field(default_factory=list)
    attribution_tier: str | None = None
    localization_status: str | None = None


class SynthesisEvaluation(BaseModel):
    """Evaluation of synthesized Playwright regression test script validity."""

    model_config = ConfigDict(extra="forbid")

    expected_synthesized: bool
    test_generated: bool = False
    structurally_validated: bool = False
    executed_successfully: bool = False
    reproduces_target: bool = False
    code_size_bytes: int = 0
    assertions_count: int = 0


class TimingMetrics(BaseModel):
    """Operational duration breakdown across investigation phases."""

    model_config = ConfigDict(extra="forbid")

    total_duration_s: float = 0.0
    phase_durations_s: dict[str, float] = Field(default_factory=dict)


class ResourceMetrics(BaseModel):
    """Resource consumption metrics during benchmark execution."""

    model_config = ConfigDict(extra="forbid")

    browser_sessions_count: int = 0
    artifacts_bytes: int = 0
    workflow_retries: int = 0
    nodes_executed: int = 0


class EvaluationResult(BaseModel):
    """Comprehensive evaluation record for a single benchmark case."""

    model_config = ConfigDict(extra="forbid")

    evaluation_id: UUID = Field(default_factory=uuid4)
    case_id: str
    workflow_id: str
    analysis_id: UUID
    end_to_end_status: EndToEndStatus
    detection: DetectionEvaluation
    classification: ClassificationEvaluation
    reproduction: ReproductionEvaluation
    root_cause: RootCauseEvaluation
    synthesis: SynthesisEvaluation
    timing: TimingMetrics = Field(default_factory=TimingMetrics)
    resources: ResourceMetrics = Field(default_factory=ResourceMetrics)
    failure_taxonomy: list[FailureTaxonomy] = Field(default_factory=list)
    deterministic_signature: str = ""
    notes: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=utc_now)


class CategoryMetricDetail(BaseModel):
    """Category-level precision, recall, and F1 counts."""

    model_config = ConfigDict(extra="forbid")

    category: str
    sample_size: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float | str  # float or "INSUFFICIENT_SAMPLE"
    recall: float | str     # float or "INSUFFICIENT_SAMPLE"
    f1: float | str         # float or "INSUFFICIENT_SAMPLE"


class EvaluationSummaryMetrics(BaseModel):
    """Aggregated evaluation metrics across a benchmark suite."""

    model_config = ConfigDict(extra="forbid")

    total_cases: int = 0
    complete_success_count: int = 0
    partial_success_count: int = 0
    inconclusive_count: int = 0
    failure_count: int = 0

    # Detection
    detection_tp: int = 0
    detection_fp: int = 0
    detection_fn: int = 0
    detection_tn: int = 0
    detection_precision: float = 0.0
    detection_recall: float = 0.0
    detection_specificity: float = 0.0
    detection_f1: float = 0.0

    # Subsystem Accuracies
    classification_accuracy: float = 0.0
    reproduction_accuracy: float = 0.0
    file_localization_accuracy: float = 0.0
    symbol_localization_accuracy: float = 0.0
    commit_attribution_accuracy: float = 0.0
    test_generation_rate: float = 0.0
    test_structural_validity_rate: float = 0.0

    # Category Breakdown & Confusion
    category_metrics: list[CategoryMetricDetail] = Field(default_factory=list)
    confusion_matrix: dict[str, dict[str, int]] = Field(default_factory=dict)

    # Failure Taxonomy Counts
    failure_taxonomy_counts: dict[str, int] = Field(default_factory=dict)

    # Stability & Determinism (for repeated runs)
    repeat_runs_total: int = 0
    identical_runs_count: int = 0
    determinism_rate: float = 1.0


class EvaluationSuiteResult(BaseModel):
    """Top-level immutable container for an entire benchmark evaluation run."""

    model_config = ConfigDict(extra="forbid")

    suite_id: str
    suite_name: str
    run_id: UUID = Field(default_factory=uuid4)
    results: list[EvaluationResult] = Field(default_factory=list)
    summary: EvaluationSummaryMetrics = Field(default_factory=EvaluationSummaryMetrics)
    environment_info: dict[str, Any] = Field(default_factory=dict)
    executed_at: datetime = Field(default_factory=utc_now)
