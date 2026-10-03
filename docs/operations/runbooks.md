# RETRACE — Operational Incident Runbooks

## 1. High API Error Rate (`HighApiErrorRate`)

- **Trigger**: `retrace_http_errors_total / retrace_http_requests_total > 5%` over 2m.
- **Severity**: Critical.
- **Diagnosis**:
  1. Check `/ready` probe to identify degraded dependencies (DB, Redis, S3).
  2. Inspect structured logs for `event_type="api.error"` and group by `path` and `error_type`.
  3. Verify ALB health check target health in AWS ECS.
- **Mitigation**:
  - If database pool exhaustion: Increase `DATABASE_POOL_SIZE` or restart frozen connections.
  - If Redis disconnected: Check ElastiCache security groups and VPC routing.

---

## 2. High API Latency (`HighApiLatency`)

- **Trigger**: p95 latency > 2.0 seconds over 3m.
- **Severity**: Warning.
- **Diagnosis**:
  1. Inspect `retrace_http_request_duration_seconds` by route.
  2. If heavy artifact downloads: Verify S3 prefix caching or CDN enablement.
  3. Inspect PostgreSQL slow queries and connection wait times.

---

## 3. Worker Failure Spike (`WorkerFailureSpike`)

- **Trigger**: Worker job failure rate > 0.2 jobs/sec over 2m.
- **Severity**: Critical.
- **Diagnosis**:
  1. Check worker logs for `event_type="worker.job.failed"`.
  2. Verify target application base URLs (`version_a.base_url`, `version_b.base_url`) are reachable from ECS VPC.
  3. Check Chromium sandboxing and memory usage (`container_memory_working_set_bytes`).
- **Mitigation**:
  - Scale up ECS worker task desired count if concurrency limit reached.
  - Fix blocked network policies if target lab hosts are firewalled.

---

## 4. Redis Stream Queue Backlog (`RedisQueueBacklog`)

- **Trigger**: `retrace_queue_depth > 50` over 5m.
- **Severity**: Warning.
- **Diagnosis**:
  1. Check active worker consumer count via `retrace_queue_processing`.
  2. Check if workers crashed or deadlocked on browser tasks.
- **Mitigation**:
  - Restart dead worker tasks. Recover pending jobs via automated `XAUTOCLAIM`.
  - Increase ECS worker service desired count.

---

## 5. Database / Redis Connectivity Failure

- **Trigger**: `DatabaseConnectivityDegraded` or `RedisConnectivityDegraded`.
- **Severity**: Critical.
- **Diagnosis**:
  1. Verify RDS / ElastiCache cluster health in AWS Console.
  2. Check subnet routing and security group rules between ECS Fargate tasks and data subnets.
- **Mitigation**:
  - Failover to Multi-AZ standby replica if primary node hardware failure occurs.
