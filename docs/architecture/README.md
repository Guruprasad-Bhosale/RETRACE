# RETRACE Architecture Blueprint

## 1. System Overview

**RETRACE** is an autonomous, evidence-driven regression investigation platform. It explores two versions of a web application (Version A vs. Version B), identifies meaningful behavioral and API contract regressions, eliminates cosmetic noise, reproduces failures through isolated Playwright scripts, investigates root causes using source code AST diffs, and synthesizes engineering reports with full evidence provenance.

```mermaid
graph TD
    FE[Angular 22+ Frontend Command Center] -->|HTTP REST / SSE / WebSocket| API[FastAPI Orchestration Gateway]
    API -->|Jobs / Events| RS[(Redis Streams Event Bus)]
    API -->|Metadata / Results| PG[(PostgreSQL + pgvector)]
    API -->|Artifacts| S3[(MinIO / S3 Artifact Store)]
    
    RS -->|Job Claim| WRK[Async Analysis Worker Pool]
    WRK -->|Autonomous Exploration| PW[Playwright Browser Automation]
    WRK -->|State Diffs & Provenance| DIFF[Semantic Diff Engine]
    WRK -->|Reproduction Scripts| REPRO[Autonomous Reproducer]
    WRK -->|AST & Git Correlation| RCA[Root Cause Analyzer]
    WRK -->|Artifact Writes| S3
    WRK -->|Status Updates| PG
```

---

## 2. Core Service Boundaries

### Frontend (`apps/frontend/`)
* **Role:** Single-page command center for configuring analysis runs, inspecting live workflows, viewing dual-pane visual replays, and exploring interactive Monaco AST diffs.
* **Boundary:** Strictly client-side. Communicates exclusively with `apps/api/` via HTTP/JSON contracts. Zero direct database or filesystem access.

### API Gateway (`apps/api/`)
* **Role:** Authentication, request validation, project management, run lifecycle triggering, health & readiness probes, and telemetry.
* **Boundary:** Stateless REST API. Dispatches long-running exploration and analysis jobs to Redis Streams. Does not execute Playwright browsers in-process.

### Analysis Worker (`apps/worker/`)
* **Role:** Execution engine for browser automation (Playwright), state diff calculation, LLM reasoning agent invocation (LangGraph), reproduction verification, and report synthesis.
* **Boundary:** Scalable background process. Consumes jobs from Redis Streams, runs isolated tasks, and writes multi-modal artifacts to object storage.

### Shared Packages (`packages/`)
* `packages/domain/`: Pure domain entities, value objects, enums, and validation logic.
* `packages/config/`: Centralized Pydantic BaseSettings loading from environment variables.
* `packages/storage/`: Abstract `ArtifactStorage` with Local and S3/MinIO backends.
* `packages/db/`: SQLAlchemy declarative base, async session management, and health probes.
* `packages/redis_client/`: Async Redis connection pooling and health checks.
* `packages/logging/`: Structured contextual logging system.

---

## 3. Evidence & Provenance Model

RETRACE is an **evidence-first** system. AI reasoning is applied *only after* deterministic evidence is captured and diffed.

Every regression finding maintains strict provenance:
```text
Observation (vA vs vB)
   ↓
Deterministic Diff (DOM, A11y, HAR, Console, Performance)
   ↓
Candidate Anomaly Classification
   ↓
Autonomous Playwright Reproduction (Must fail on vB, pass on vA)
   ↓
Git Commit & AST Diff Correlation
   ↓
Verified Engineering Report
```
