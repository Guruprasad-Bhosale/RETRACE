"""Prometheus Metrics Collector and Registry for RETRACE.

Provides high-performance, low-cardinality counters, gauges, and histograms
with Prometheus exposition format generation.
"""

import threading
from typing import Any


class Counter:
    """Thread-safe Prometheus Counter metric."""

    def __init__(self, name: str, description: str, label_names: list[str]) -> None:
        self.name = name
        self.description = description
        self.label_names = tuple(label_names)
        self._values: dict[tuple[str, ...], float] = {}
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0, **labels: Any) -> None:
        """Increment counter by specified amount."""
        key = tuple(str(labels.get(k, "unknown")) for k in self.label_names)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + amount

    def get(self, **labels: Any) -> float:
        key = tuple(str(labels.get(k, "unknown")) for k in self.label_names)
        with self._lock:
            return self._values.get(key, 0.0)

    def collect(self) -> list[str]:
        lines = [f"# HELP {self.name} {self.description}", f"# TYPE {self.name} counter"]
        with self._lock:
            if not self._values and not self.label_names:
                lines.append(f"{self.name} 0.0")
            for label_vals, val in sorted(self._values.items()):
                if self.label_names:
                    label_str = ",".join(
                        f'{k}="{v}"' for k, v in zip(self.label_names, label_vals, strict=False)
                    )
                    lines.append(f"{self.name}{{{label_str}}} {val}")
                else:
                    lines.append(f"{self.name} {val}")
        return lines


class Gauge:
    """Thread-safe Prometheus Gauge metric."""

    def __init__(self, name: str, description: str, label_names: list[str]) -> None:
        self.name = name
        self.description = description
        self.label_names = tuple(label_names)
        self._values: dict[tuple[str, ...], float] = {}
        self._lock = threading.Lock()

    def set(self, value: float, **labels: Any) -> None:
        """Set gauge to specified value."""
        key = tuple(str(labels.get(k, "unknown")) for k in self.label_names)
        with self._lock:
            self._values[key] = float(value)

    def inc(self, amount: float = 1.0, **labels: Any) -> None:
        key = tuple(str(labels.get(k, "unknown")) for k in self.label_names)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + amount

    def dec(self, amount: float = 1.0, **labels: Any) -> None:
        key = tuple(str(labels.get(k, "unknown")) for k in self.label_names)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) - amount

    def get(self, **labels: Any) -> float:
        key = tuple(str(labels.get(k, "unknown")) for k in self.label_names)
        with self._lock:
            return self._values.get(key, 0.0)

    def collect(self) -> list[str]:
        lines = [f"# HELP {self.name} {self.description}", f"# TYPE {self.name} gauge"]
        with self._lock:
            if not self._values and not self.label_names:
                lines.append(f"{self.name} 0.0")
            for label_vals, val in sorted(self._values.items()):
                if self.label_names:
                    label_str = ",".join(
                        f'{k}="{v}"' for k, v in zip(self.label_names, label_vals, strict=False)
                    )
                    lines.append(f"{self.name}{{{label_str}}} {val}")
                else:
                    lines.append(f"{self.name} {val}")
        return lines


class Histogram:
    """Thread-safe Prometheus Histogram metric."""

    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)

    def __init__(
        self,
        name: str,
        description: str,
        label_names: list[str],
        buckets: tuple[float, ...] = DEFAULT_BUCKETS,
    ) -> None:
        self.name = name
        self.description = description
        self.label_names = tuple(label_names)
        self.buckets = sorted(buckets)
        self._counts: dict[tuple[str, ...], int] = {}
        self._sums: dict[tuple[str, ...], float] = {}
        self._bucket_counts: dict[tuple[str, ...], dict[float, int]] = {}
        self._lock = threading.Lock()

    def observe(self, amount: float, **labels: Any) -> None:
        """Record an observed value."""
        key = tuple(str(labels.get(k, "unknown")) for k in self.label_names)
        with self._lock:
            self._counts[key] = self._counts.get(key, 0) + 1
            self._sums[key] = self._sums.get(key, 0.0) + amount

            if key not in self._bucket_counts:
                self._bucket_counts[key] = dict.fromkeys(self.buckets, 0)

            for b in self.buckets:
                if amount <= b:
                    self._bucket_counts[key][b] += 1

    def collect(self) -> list[str]:
        lines = [f"# HELP {self.name} {self.description}", f"# TYPE {self.name} histogram"]
        with self._lock:
            for key in sorted(self._counts.keys()):
                base_labels = [
                    f'{k}="{v}"' for k, v in zip(self.label_names, key, strict=False)
                ] if self.label_names else []

                cumulative = 0
                for b in self.buckets:
                    cumulative = self._bucket_counts[key].get(b, 0)
                    b_label = f'le="{b}"'
                    all_labels = [*base_labels, b_label]
                    lines.append(f"{self.name}_bucket{{{','.join(all_labels)}}} {cumulative}")

                inf_labels = [*base_labels, 'le="+Inf"']
                lines.append(f"{self.name}_bucket{{{','.join(inf_labels)}}} {self._counts[key]}")
                lines.append(f"{self.name}_sum{{{','.join(base_labels)}}} {self._sums[key]}")
                lines.append(f"{self.name}_count{{{','.join(base_labels)}}} {self._counts[key]}")
        return lines


class MetricsRegistry:
    """Central registry holding all operational Prometheus metrics."""

    def __init__(self) -> None:
        # API Metrics
        self.http_requests_total = Counter(
            "retrace_http_requests_total",
            "Total HTTP requests handled by the API",
            ["method", "route", "status"],
        )
        self.http_request_duration_seconds = Histogram(
            "retrace_http_request_duration_seconds",
            "HTTP request latency in seconds",
            ["method", "route"],
        )
        self.http_errors_total = Counter(
            "retrace_http_errors_total",
            "Total HTTP error responses returned",
            ["method", "route", "error_type"],
        )

        # Analysis Metrics
        self.analyses_started_total = Counter(
            "retrace_analyses_started_total",
            "Total regression analyses initiated",
            ["status"],
        )
        self.analyses_completed_total = Counter(
            "retrace_analyses_completed_total",
            "Total regression analyses successfully completed",
            ["status"],
        )
        self.analyses_failed_total = Counter(
            "retrace_analyses_failed_total",
            "Total regression analyses failed",
            ["reason"],
        )
        self.analysis_duration_seconds = Histogram(
            "retrace_analysis_duration_seconds",
            "Duration of regression analyses in seconds",
            ["phase"],
        )

        # Worker Metrics
        self.worker_jobs_claimed_total = Counter(
            "retrace_worker_jobs_claimed_total",
            "Total background jobs claimed by workers",
            ["job_type"],
        )
        self.worker_jobs_completed_total = Counter(
            "retrace_worker_jobs_completed_total",
            "Total background jobs completed by workers",
            ["status"],
        )
        self.worker_jobs_failed_total = Counter(
            "retrace_worker_jobs_failed_total",
            "Total background jobs failed by workers",
            ["error_type"],
        )
        self.worker_job_duration_seconds = Histogram(
            "retrace_worker_job_duration_seconds",
            "Worker job execution duration in seconds",
            ["job_type"],
        )

        # Queue Metrics
        self.queue_depth = Gauge(
            "retrace_queue_depth",
            "Current pending message count in Redis stream queue",
            ["stream_key"],
        )
        self.queue_processing = Gauge(
            "retrace_queue_processing",
            "Current messages actively being processed by workers",
            ["consumer_group"],
        )
        self.queue_failures_total = Counter(
            "retrace_queue_failures_total",
            "Total queue delivery or retry failures",
            ["stream_key"],
        )

        # Browser Execution Metrics
        self.browser_sessions_total = Counter(
            "retrace_browser_sessions_total",
            "Total Playwright browser sessions launched",
            ["version"],
        )
        self.browser_failures_total = Counter(
            "retrace_browser_failures_total",
            "Total Playwright browser action or navigation failures",
            ["failure_type"],
        )
        self.browser_duration_seconds = Histogram(
            "retrace_browser_duration_seconds",
            "Duration of browser actions in seconds",
            ["action_type"],
        )

        # Storage Metrics
        self.artifacts_created_total = Counter(
            "retrace_artifacts_created_total",
            "Total investigation artifacts written to storage",
            ["artifact_type"],
        )
        self.artifacts_bytes_total = Counter(
            "retrace_artifacts_bytes_total",
            "Total bytes written to artifact storage",
            ["artifact_type"],
        )
        self.artifact_failures_total = Counter(
            "retrace_artifact_failures_total",
            "Total artifact storage write or read failures",
            ["failure_type"],
        )

    def generate_exposition(self) -> str:
        """Render all metrics in Prometheus text exposition format."""
        all_metrics = [
            self.http_requests_total,
            self.http_request_duration_seconds,
            self.http_errors_total,
            self.analyses_started_total,
            self.analyses_completed_total,
            self.analyses_failed_total,
            self.analysis_duration_seconds,
            self.worker_jobs_claimed_total,
            self.worker_jobs_completed_total,
            self.worker_jobs_failed_total,
            self.worker_job_duration_seconds,
            self.queue_depth,
            self.queue_processing,
            self.queue_failures_total,
            self.browser_sessions_total,
            self.browser_failures_total,
            self.browser_duration_seconds,
            self.artifacts_created_total,
            self.artifacts_bytes_total,
            self.artifact_failures_total,
        ]
        output = []
        for m in all_metrics:
            output.extend(m.collect())
            output.append("")
        return "\n".join(output)


metrics_registry = MetricsRegistry()
