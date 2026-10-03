# RETRACE Local Production-Like Profile Guide

## 1. Overview

The local production-like environment provides an exact Docker Compose replica of the AWS production stack, including PostgreSQL, Redis Streams, MinIO S3-compatible storage, FastAPI API, Analysis Worker, and Angular Nginx web server.

## 2. Prerequisites

- Docker Engine 24.0+ and Docker Compose v2.20+
- At least 8 GB RAM and 20 GB free disk space

## 3. Starting the Production-Like Environment

```bash
# Navigate to the compose directory
cd infrastructure/compose

# Build and start all services in production mode
docker compose -f docker-compose.prod.yml up -d --build

# Verify all services are healthy
docker compose -f docker-compose.prod.yml ps
```

## 4. Validating Health and Readiness

```bash
# 1. Check API Liveness
curl http://localhost:8000/health
# Response: {"status":"healthy","service":"retrace-api"}

# 2. Check API Readiness (DB + Redis + MinIO S3)
curl http://localhost:8000/ready
# Response: {"status":"ready","database":{"healthy":true},"redis":{"healthy":true},"storage":{"healthy":true}}

# 3. Check Frontend Web Server
curl http://localhost/health
# Response: {"status":"healthy","service":"retrace-frontend"}
```

## 5. Running Pre-flight Configuration Validation

```bash
# Run the configuration validator inside the API container
docker compose -f docker-compose.prod.yml exec api python -m apps.api.config_check --environment production
```

## 6. Teardown & Reset

```bash
# Stop all containers
docker compose -f docker-compose.prod.yml down

# Full reset including volume data
docker compose -f docker-compose.prod.yml down -v
```
