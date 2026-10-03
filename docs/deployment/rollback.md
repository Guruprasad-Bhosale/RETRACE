# RETRACE Production Rollback & Emergency Recovery Runbook

## 1. Rollback Triggers

A rollback must be initiated immediately if:
- API `/health` or `/ready` error rate exceeds 1% post-deployment.
- ECS task crash loops occur during task startup.
- Unhandled 500 errors spike in CloudWatch logs.
- Post-deployment smoke tests fail.

## 2. Fast Rollback Procedure (Container Version Reversion)

Because image tags are immutable (Git SHA), rolling back to the previous stable release takes under 2 minutes:

```bash
# 1. Identify previous stable image SHA
PREVIOUS_STABLE_SHA="<PREVIOUS_GIT_SHA>"

# 2. Update ECS Services to previous task definition revision
aws ecs update-service --cluster retrace-production-cluster \
  --service retrace-production-api-service \
  --task-definition retrace-production-api:${PREVIOUS_STABLE_REVISION}

aws ecs update-service --cluster retrace-production-cluster \
  --service retrace-production-worker-service \
  --task-definition retrace-production-worker:${PREVIOUS_STABLE_REVISION}

aws ecs update-service --cluster retrace-production-cluster \
  --service retrace-production-frontend-service \
  --task-definition retrace-production-frontend:${PREVIOUS_STABLE_REVISION}
```

## 3. Database Migration Rollback

If a database schema change needs to be rolled back:
```bash
# Rollback one migration revision
python -m packages.db.migrations --rollback

# Or target specific revision ID
python -m packages.db.migrations --rollback --revision <TARGET_REVISION_ID>
```

> **Note**: Database schema changes in RETRACE are backwards-compatible (expand/contract pattern). Schema migrations should not drop columns in the same release where code references are removed.

## 4. Post-Rollback Verification

1. Check `/health` and `/ready` endpoints.
2. Verify active worker consumer count in Redis Streams (`XINFO GROUPS retrace:analysis:jobs`).
3. Run smoke tests: `pytest tests/integration/smoke/test_production_smoke.py -v`.
