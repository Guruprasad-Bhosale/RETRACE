# RETRACE Production Deployment Guide (AWS ECS Fargate)

## 1. Deployment Strategy

RETRACE uses immutable container tags (Git SHA), Blue/Green rolling deployments on AWS ECS Fargate, and pre-flight migration safety gates.

## 2. Step-by-Step Production Release Workflow

### Step 1: Pre-flight Verification & Quality Gates
Before any deployment, CI runs:
1. `ruff check .` (Static code quality)
2. `python -m packages.security.audit` (Secret & vulnerability scan)
3. `python -m packages.config.validator` (Production configuration check)
4. `pytest -v` (Full backend unit, integration, and Phase 13 benchmark tests)
5. `npm test -- --watch=false` and `npm run build` (Frontend unit tests & build)

### Step 2: Database Migration Check & Execution
Apply database schema updates before rolling out new application tasks:
```bash
# Verify single migration head
python -m packages.db.migrations --check

# Apply migrations
python -m packages.db.migrations --apply
```

### Step 3: Build & Push Immutable Container Images
```bash
# Tag images with commit SHA
GIT_SHA=$(git rev-parse --short HEAD)

# API
docker build -t ${ECR_URL}/retrace-api:${GIT_SHA} -f infrastructure/docker/Dockerfile.api .
docker push ${ECR_URL}/retrace-api:${GIT_SHA}

# Worker
docker build -t ${ECR_URL}/retrace-worker:${GIT_SHA} -f infrastructure/docker/Dockerfile.worker .
docker push ${ECR_URL}/retrace-worker:${GIT_SHA}

# Frontend
docker build -t ${ECR_URL}/retrace-frontend:${GIT_SHA} -f infrastructure/docker/Dockerfile.frontend .
docker push ${ECR_URL}/retrace-frontend:${GIT_SHA}
```

### Step 4: ECS Service Update (Rolling Zero-Downtime Deployment)
```bash
# Update API task definition and service
aws ecs update-service --cluster retrace-production-cluster \
  --service retrace-production-api-service \
  --force-new-deployment

# Update Worker service
aws ecs update-service --cluster retrace-production-cluster \
  --service retrace-production-worker-service \
  --force-new-deployment

# Update Frontend service
aws ecs update-service --cluster retrace-production-cluster \
  --service retrace-production-frontend-service \
  --force-new-deployment
```

### Step 5: Post-Deployment Smoke Test
Run automated smoke test validating health probes, readiness checks, and job execution:
```bash
pytest tests/integration/smoke/test_production_smoke.py -v
```
