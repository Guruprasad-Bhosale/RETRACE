"""RETRACE Benchmark Baseline Manager.

Provides storage, snapshotting, and regression comparison between active
benchmark evaluation runs and committed historical baselines.
"""

import json
from pathlib import Path
from typing import Any

from apps.worker.evaluation.models import EvaluationSummaryMetrics


class EvaluationBaselineManager:
    """Manages evaluation baseline snapshots and detects performance regressions."""

    def __init__(self, baseline_path: Path | str | None = None) -> None:
        if baseline_path is None:
            self.baseline_path = Path(__file__).resolve().parent.parent.parent.parent / "benchmarks" / "benchmark-baseline.json"
        else:
            self.baseline_path = Path(baseline_path)

    def load_baseline(self) -> EvaluationSummaryMetrics | None:
        """Load baseline metrics from disk if present."""
        if not self.baseline_path.exists():
            return None
        try:
            with self.baseline_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return EvaluationSummaryMetrics(**data)
        except Exception:
            return None

    def save_baseline(self, summary: EvaluationSummaryMetrics) -> None:
        """Save a new baseline summary snapshot to disk."""
        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)
        with self.baseline_path.open("w", encoding="utf-8") as f:
            json.dump(summary.model_dump(mode="json"), f, indent=2)

    def compare(
        self, current_summary: EvaluationSummaryMetrics
    ) -> dict[str, Any]:
        """Compare current evaluation summary against historical baseline."""
        baseline = self.load_baseline()
        if baseline is None:
            return {
                "status": "NO_BASELINE",
                "message": "No historical baseline found; current run established as new baseline.",
                "improvements_count": 0,
                "regressions_count": 0,
                "metric_diffs": {},
            }

        diffs: dict[str, dict[str, Any]] = {}
        improvements = 0
        regressions = 0

        # Numerical comparison metrics
        comparable_metrics = [
            ("detection_precision", True),
            ("detection_recall", True),
            ("detection_specificity", True),
            ("classification_accuracy", True),
            ("reproduction_accuracy", True),
            ("file_localization_accuracy", True),
            ("symbol_localization_accuracy", True),
            ("commit_attribution_accuracy", True),
            ("test_generation_rate", True),
            ("test_structural_validity_rate", True),
            ("determinism_rate", True),
            ("detection_fp", False),  # Lower is better
            ("detection_fn", False),  # Lower is better
            ("failure_count", False), # Lower is better
        ]

        for metric_name, higher_is_better in comparable_metrics:
            curr_val = getattr(current_summary, metric_name, 0.0)
            base_val = getattr(baseline, metric_name, 0.0)
            delta = round(curr_val - base_val, 4)

            if delta != 0:
                if higher_is_better:
                    is_improved = delta > 0
                else:
                    is_improved = delta < 0

                if is_improved:
                    status = "IMPROVED"
                    improvements += 1
                else:
                    status = "REGRESSED"
                    regressions += 1

                diffs[metric_name] = {
                    "baseline": base_val,
                    "current": curr_val,
                    "delta": delta,
                    "status": status,
                }

        overall_status = "UNCHANGED"
        if regressions > 0:
            overall_status = "REGRESSED"
        elif improvements > 0:
            overall_status = "IMPROVED"

        return {
            "status": overall_status,
            "improvements_count": improvements,
            "regressions_count": regressions,
            "metric_diffs": diffs,
        }
