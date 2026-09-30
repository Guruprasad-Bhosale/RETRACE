"""RETRACE Evaluation Metrics Engine.

Provides deterministic calculations for detection accuracy, category confusion
matrices, reproduction rates, source localization precision, and repeated-run stability.
"""

from collections import defaultdict

from apps.worker.evaluation.models import (
    CategoryMetricDetail,
    DetectionEvaluation,
    EvaluationResult,
    EvaluationSummaryMetrics,
)
from benchmarks.models import ExpectedOutcome


def evaluate_detection(expected_outcome: ExpectedOutcome, detected_regression: bool) -> DetectionEvaluation:
    """Evaluate whether a regression detection was a true/false positive or negative."""
    is_expected = expected_outcome == ExpectedOutcome.REGRESSION

    tp = is_expected and detected_regression
    fp = (not is_expected) and detected_regression
    fn = is_expected and (not detected_regression)
    tn = (not is_expected) and (not detected_regression)

    return DetectionEvaluation(
        is_regression_expected=is_expected,
        is_regression_detected=detected_regression,
        true_positive=tp,
        false_positive=fp,
        false_negative=fn,
        true_negative=tn,
    )


def compute_confusion_matrix(results: list[EvaluationResult]) -> dict[str, dict[str, int]]:
    """Construct an empirical confusion matrix mapping expected to observed categories."""
    matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for res in results:
        expected = res.classification.expected_category.upper()
        observed = (res.classification.observed_category or "NONE").upper()
        matrix[expected][observed] += 1

    # Convert to standard dict
    return {k: dict(v) for k, v in matrix.items()}


def compute_category_metrics(
    results: list[EvaluationResult], min_sample_size: int = 2
) -> list[CategoryMetricDetail]:
    """Compute per-category precision, recall, and F1 with strict insufficient sample reporting."""
    categories: set[str] = {r.classification.expected_category.upper() for r in results if r.classification.expected_category}

    details: list[CategoryMetricDetail] = []

    for cat in sorted(categories):
        tp = 0
        fp = 0
        fn = 0
        sample_size = 0

        for r in results:
            exp = r.classification.expected_category.upper()
            obs = (r.classification.observed_category or "").upper()

            if exp == cat:
                sample_size += 1
                if obs == cat:
                    tp += 1
                else:
                    fn += 1
            else:
                if obs == cat:
                    fp += 1

        if sample_size < min_sample_size:
            prec_val: float | str = "INSUFFICIENT_SAMPLE"
            rec_val: float | str = "INSUFFICIENT_SAMPLE"
            f1_val: float | str = "INSUFFICIENT_SAMPLE"
        else:
            prec = float(tp) / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = float(tp) / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
            prec_val = round(prec, 4)
            rec_val = round(rec, 4)
            f1_val = round(f1, 4)

        details.append(
            CategoryMetricDetail(
                category=cat,
                sample_size=sample_size,
                true_positives=tp,
                false_positives=fp,
                false_negatives=fn,
                precision=prec_val,
                recall=rec_val,
                f1=f1_val,
            )
        )

    return details


def summarize_suite_metrics(
    results: list[EvaluationResult],
    repeat_runs_total: int = 0,
    identical_runs_count: int = 0,
) -> EvaluationSummaryMetrics:
    """Aggregate individual case evaluations into a comprehensive suite summary."""
    total = len(results)
    if total == 0:
        return EvaluationSummaryMetrics()

    # Status counts
    complete_success = sum(1 for r in results if r.end_to_end_status.value == "COMPLETE_SUCCESS")
    partial_success = sum(1 for r in results if r.end_to_end_status.value == "PARTIAL_SUCCESS")
    inconclusive = sum(1 for r in results if r.end_to_end_status.value == "INCONCLUSIVE")
    failure = sum(1 for r in results if r.end_to_end_status.value == "FAILURE")

    # Detection counts
    tp = sum(1 for r in results if r.detection.true_positive)
    fp = sum(1 for r in results if r.detection.false_positive)
    fn = sum(1 for r in results if r.detection.false_negative)
    tn = sum(1 for r in results if r.detection.true_negative)

    prec = float(tp) / (tp + fp) if (tp + fp) > 0 else 1.0 if fp == 0 else 0.0
    rec = float(tp) / (tp + fn) if (tp + fn) > 0 else 1.0 if fn == 0 else 0.0
    spec = float(tn) / (tn + fp) if (tn + fp) > 0 else 1.0
    f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

    # Subsystem Rates
    class_acc = sum(1 for r in results if r.classification.category_matched) / total
    repro_acc = sum(1 for r in results if r.reproduction.reproduction_matched) / total
    file_loc_acc = sum(1 for r in results if r.root_cause.file_matched) / total
    sym_loc_acc = sum(1 for r in results if r.root_cause.symbol_matched) / total
    commit_acc = sum(1 for r in results if r.root_cause.commit_matched) / total
    test_gen_rate = sum(1 for r in results if r.synthesis.test_generated) / total
    test_struct_rate = sum(1 for r in results if r.synthesis.structurally_validated) / total

    # Failure Taxonomy Counts
    taxonomy_counts: dict[str, int] = defaultdict(int)
    for r in results:
        for f in r.failure_taxonomy:
            taxonomy_counts[f.value] += 1

    # Determinism Rate
    det_rate = (
        float(identical_runs_count) / repeat_runs_total
        if repeat_runs_total > 0
        else 1.0
    )

    return EvaluationSummaryMetrics(
        total_cases=total,
        complete_success_count=complete_success,
        partial_success_count=partial_success,
        inconclusive_count=inconclusive,
        failure_count=failure,
        detection_tp=tp,
        detection_fp=fp,
        detection_fn=fn,
        detection_tn=tn,
        detection_precision=round(prec, 4),
        detection_recall=round(rec, 4),
        detection_specificity=round(spec, 4),
        detection_f1=round(f1, 4),
        classification_accuracy=round(class_acc, 4),
        reproduction_accuracy=round(repro_acc, 4),
        file_localization_accuracy=round(file_loc_acc, 4),
        symbol_localization_accuracy=round(sym_loc_acc, 4),
        commit_attribution_accuracy=round(commit_acc, 4),
        test_generation_rate=round(test_gen_rate, 4),
        test_structural_validity_rate=round(test_struct_rate, 4),
        category_metrics=compute_category_metrics(results),
        confusion_matrix=compute_confusion_matrix(results),
        failure_taxonomy_counts=dict(taxonomy_counts),
        repeat_runs_total=repeat_runs_total,
        identical_runs_count=identical_runs_count,
        determinism_rate=round(det_rate, 4),
    )
