# RETRACE Production Architecture & Cloud Operations

## 1. System Overview

RETRACE is deployed as a modular, containerized, multi-tiered cloud architecture designed for high availability, deterministic investigation isolation, and zero-trust sandbox execution.

```text
                                  Internet
                                     │
                                     ▼
                      AWS Application Load Balancer (ALB)
                       ├── /api/*  ──► ECS API Target Group (Port 8000)
                       └── /*      ──► ECS Frontend Target Group (Port 80)
                                     │
                 ┌───────────────────┴───────────────────┐
                 │                                       │
                 ▼                                       ▼
     [ECS Service: API] (Fargate)            [ECS Service: Frontend]
     • FastAPI ASGI Runtime                  • Angular Command Center SPA
     • Request Audit & Tracing               • Hardened Nginx 1.25 Alpine
     • LangGraph State Access                • Static Asset Compression & Caching
                 │
                 ├── Enqueues Jobs (XADD)
                 │
                 ▼
     [Amazon ElastiCache Redis / Valkey]
     • Multi-AZ Replication Group
     • Redis Streams (`retrace:analysis:jobs`)
     • Consumer Group (`retrace-worker-group`)
                 ▲
                 │ Consumes Jobs (XREADGROUP / XAUTOCLAIM)
                 │
     [ECS Service: Analysis Worker] (Fargate)
     • Autonomous Exploration & Replay
     • Headless Chromium Sandbox
     • Deterministic Diffing & Root Cause Engine
     • Test Synthesis Engine
                 │
        ┌────────┴────────┐
        ▼                 ▼
[Amazon RDS PostgreSQL] [Amazon S3 Artifact Storage]
• PostgreSQL 16 Multi-AZ • `retrace-prod-artifacts`
• Alembic Managed Schema • SHA-256 Verified Traces
• Investigation Metadata • AES-256 Server-Side Encryption
• Checkpoint State Store • 90-Day Lifecycle Retention
```

## 2. Infrastructure Components

| Subsystem | Managed AWS Service | Local Development Equivalent | Sizing / Spec |
| :--- | :--- | :--- | :--- |
| **Ingress & TLS** | AWS Application Load Balancer | Docker Compose Port Mapping | Multi-AZ Public Subnets |
| **API Runtime** | AWS ECS Fargate | Docker API Container | 1 vCPU, 2 GB RAM (Autoscaled) |
| **Worker Runtime** | AWS ECS Fargate | Docker Worker Container | 2 vCPU, 4 GB RAM (Autoscaled) |
| **Frontend UI** | AWS ECS Fargate (Nginx) | Docker Frontend Container | 0.5 vCPU, 1 GB RAM |
| **Message Queue** | Amazon ElastiCache Redis | Redis 7.4 Alpine | `cache.t4g.small` Multi-AZ |
| **Database** | Amazon RDS PostgreSQL 16 | PostgreSQL 16 + pgvector | `db.t4g.medium` Multi-AZ (50-200GB) |
| **Artifacts** | Amazon S3 | MinIO Object Storage | AES256 Encrypted Private Bucket |
| **Secrets** | AWS Secrets Manager / SSM | `.env` File (Local Only) | Encrypted KMS Secret Store |
| **Logs & Metrics**| Amazon CloudWatch Logs | Docker Stdout JSON Logs | 30-Day Retention |

## 3. Data Flow & Separation of Concerns

1. **User Request**: Operator triggers or queries an investigation via the Angular Command Center or REST API.
2. **State & Queue**: API validates the request, creates database metadata in RDS, and publishes a job payload to the Redis Stream.
3. **Worker Pickup**: Worker claims the job from the Redis Stream consumer group with reliable acknowledgement (`XACK`) and automatic crash recovery (`XAUTOCLAIM`).
4. **Sandboxed Execution**: Worker spins up isolated Playwright headless browsers, executes trajectory exploration and replay against target application versions, and strictly blocks metadata service / private network exfiltration.
5. **Artifact Storage**: Screenshots, DOM snapshots, network traces, and synthesized tests are uploaded directly to S3 with SHA-256 checksum validation.
6. **State Persistence**: LangGraph checkpoints and final `InvestigationResult` records are committed to RDS.
