# RETRACE Production Troubleshooting & Diagnostic Runbook

## 1. Fast Diagnostic Matrix

| Symptom | Probable Cause | Diagnostic Command / Action |
| :--- | :--- | :--- |
| **API `/ready` returns 503** | PostgreSQL, Redis, or S3 unreachable | Check response JSON payload: `curl -s http://localhost:8000/ready` |
| **Worker not picking up jobs** | Redis consumer group missing or backlog idle | Inspect Redis group: `redis-cli XINFO GROUPS retrace:analysis:jobs` |
| **Worker crashes during browser run** | Memory limit exceeded or browser sandbox killed | Inspect worker logs in CloudWatch `/ecs/retrace-production-worker` |
| **Artifact upload fails** | S3 bucket permission or endpoint error | Check IAM task role S3 policy and bucket name configuration |
| **Migration failure on deploy** | Multiple heads or dirty migration state | Run `python -m packages.db.migrations --check` |

## 2. Common Scenarios & Remediation

### Scenario A: Pending Messages Accumulated in Redis Stream
If a worker crashes mid-investigation, unacknowledged messages enter the pending list:
```bash
# Check pending entries
redis-cli XPENDING retrace:analysis:jobs retrace-worker-group

# Active workers automatically claim idle pending jobs after REDIS_JOB_TIMEOUT_S via XAUTOCLAIM
```

### Scenario B: Tracing a Request by Correlation ID
Every HTTP request generates an `X-Request-ID` header. To trace all worker, graph, and API logs for a given request:
```bash
# In CloudWatch Insights:
fields @timestamp, @message
| filter request_id = 'req-uuid-here' or analysis_id = 'analysis-uuid-here'
| sort @timestamp asc
```
