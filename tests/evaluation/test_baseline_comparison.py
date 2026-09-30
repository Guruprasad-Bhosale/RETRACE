"""Unit tests for EvaluationBaselineManager."""

import tempfile
from pathlib import Path

from apps.worker.evaluation.baseline import EvaluationBaselineManager
from apps.worker.evaluation.models import EvaluationSummaryMetrics


def test_baseline_save_load_and_comparison():
    with tempfile.TemporaryDirectory() as tmp_dir:
        b_path = Path(tmp_dir) / "baseline.json"
        mgr = EvaluationBaselineManager(baseline_path=b_path)

        base_summary = EvaluationSummaryMetrics(
            total_cases=10,
            detection_precision=0.90,
            detection_recall=0.85,
            classification_accuracy=0.80,
        )
        mgr.save_baseline(base_summary)

        loaded = mgr.load_baseline()
        assert loaded is not None
        assert loaded.detection_precision == 0.90

        # Current run with improved metrics
        current_summary = EvaluationSummaryMetrics(
            total_cases=10,
            detection_precision=0.95,  # Improved
            detection_recall=0.85,     # Unchanged
            classification_accuracy=0.75, # Regressed
        )

        diff = mgr.compare(current_summary)
        assert diff["status"] == "REGRESSED"
        assert diff["improvements_count"] == 1
        assert diff["regressions_count"] == 1
        assert diff["metric_diffs"]["detection_precision"]["status"] == "IMPROVED"
        assert diff["metric_diffs"]["classification_accuracy"]["status"] == "REGRESSED"
