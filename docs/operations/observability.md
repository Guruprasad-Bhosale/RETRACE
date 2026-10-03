# RETRACE — Operational Telemetry & Observability Architecture

## 1. Overview & Separation Invariant

RETRACE enforces a fundamental distinction between two data classes:

1. **Investigation Evidence (Regression Analysis Subsystem)**:
   - Browser DOM state snapshots, semantic diffs, HAR logs, network requests, Playwright execution traces, AST modifications, synthesized test scripts, and markdown evidence reports.
   - **Properties**: Immutable, deterministic, traceable, cryptographically hashed (SHA-256).

2. **Operational Telemetry (Platform Monitoring Subsystem)**:
   - Request rates, latencies, CPU/Memory utilization, Redis queue depth, worker throughput, container restarts, and database connection pools.
   - **Properties**: Ephemeral, sampled, Prometheus-compatible, low cardinality.

> [!CRITICAL]
> **Zero Evidence Contamination Invariant**:
> Operational telemetry data is NEVER ingested into the regression analysis pipeline, diff engine, or root cause localization. Telemetry cannot create, alter, or substantiate a regression claim.

---

## 2. Distributed Request Correlation

Every inbound API request is tagged with correlation identifiers:
- `request_id` (`X-Request-ID` header, UUID v4)
- `trace_id` (`X-Trace-ID` header, 32-character hex)
- `organization_id` (`X-Organization-ID`)
- `user_id` (`X-User-ID`)

These identifiers are propagated across the pipeline:
```text
FastAPI Request
   │ (Sets ContextVars & TelemetrySpan)
   ▼
Redis Stream Job Payload
   │ (XADD with request_id & trace_id)
   ▼
Analysis Worker
   │ (Restores ContextVars & TelemetrySpan)
   ▼
Browser & Artifact Generation
   │ (Logged with correlation context)
```

---

## 3. Prometheus Metrics Inventory

All metrics use bounded, low-cardinality labels (no raw URLs, user IDs, or commit hashes as labels).

| Metric Name | Type | Labels | Description |
|:---|:---:|:---|:---|
| `retrace_http_requests_total` | Counter | `method`, `route`, `status` | Total HTTP requests handled |
| `retrace_http_request_duration_seconds` | Histogram | `method`, `route` | Request latency distribution |
| `retrace_http_errors_total` | Counter | `method`, `route`, `error_type` | Total error responses |
| `retrace_analyses_started_total` | Counter | `status` | Total analyses initiated |
| `retrace_analyses_completed_total` | Counter | `status` | Total analyses completed |
| `retrace_analyses_failed_total` | Counter | `reason` | Total analyses failed |
| `retrace_analysis_duration_seconds` | Histogram | `phase` | Duration of each analysis phase |
| `retrace_worker_jobs_claimed_total` | Counter | `job_type` | Total jobs claimed by workers |
| `retrace_worker_jobs_completed_total` | Counter | `status` | Total jobs completed |
| `retrace_worker_jobs_failed_total` | Counter | `error_type` | Total worker failures |
| `retrace_worker_job_duration_seconds` | Histogram | `job_type` | Job execution duration |
| `retrace_queue_depth` | Gauge | `stream_key` | Current pending stream length |
| `retrace_queue_processing` | Gauge | `consumer_group` | Messages actively being processed |
| `retrace_queue_failures_total` | Counter | `stream_key` | Queue delivery errors |
| `retrace_browser_sessions_total` | Counter | `version` | Browser sessions launched |
| `retrace_browser_failures_total` | Counter | `failure_type` | Browser navigation/action errors |
| `retrace_browser_duration_seconds` | Histogram | `action_type` | Browser action durations |
| `retrace_artifacts_created_total` | Counter | `artifact_type` | Artifacts stored |
| `retrace_artifacts_bytes_total` | Counter | `artifact_type` | Total artifact bytes stored |
| `retrace_artifact_failures_total` | Counter | `failure_type` | Storage failures |

---

## 4. Grafana Dashboards

Located in `infrastructure/observability/dashboards/`:
1. **01-retrace-overview.json**: API traffic, error rates, p50/p95 latency, active analyses, Redis queue depth.
2. **02-analysis-operations.json**: Analysis phase durations, browser actions, artifact ingestion rate.
3. **03-worker-queue.json**: Stream backlog, active worker consumers, job throughput, failure rates.
4. **04-infrastructure.json**: ECS CPU/Memory, RDS connections, Redis memory.
