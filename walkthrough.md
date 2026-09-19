# Walkthrough: Phase 1 — Core Domain Model, Persistence & Repository Layer

## Summary of Accomplishments

Phase 1 transformed the initial scaffolding into a strongly typed, trajectory-aware domain engine, a relational persistence schema with zero blob overhead, and a thin, domain-specific repository layer with optimistic concurrency control.

---

## 1. Architecture & Domain Highlights

### Sequence & Trajectory Semantics
Browser interactions and observations are modeled as an ordered state trajectory:
$$\text{Observation}_0 \xrightarrow{\text{Action}_1} \text{Observation}_1 \xrightarrow{\text{Action}_2} \text{Observation}_2 \dots$$
- Linked via `trajectory_id`, `step_index`, `prior_observation_id`, and `caused_by_action_id`.

### Deep Application State & First-Class Artifact References
- [packages/domain/models.py](file:///g:/RETRACE/packages/domain/models.py):
  - `ArtifactReference`: Strongly typed pointer to multi-modal storage (`kind`: screenshot, dom_snapshot, har_trace, playwright_trace, console_log, etc.) with URI, MIME type, size, and hash.
  - `ApplicationStateSnapshot`: Captures URL, page title, HTTP status, viewport, DOM tree hash, ARIA accessibility summary, console error counts, network request metrics, and interactive element counts.
  - `Provenance`: Full provenance metadata (`analysis_id`, `version_id`, `trajectory_id`, `step_index`, `collected_at`, `collector_service`, `environment_context`).

### Multi-Attempt Reproductions & Distinct Root Causes
- `Finding`: Links multiple `ReproductionAttempt` items ($1:N$) with attempt numbers, framework targets, execution logs, and statuses (`succeeded`, `failed`, `error`, `skipped`).
- `RootCause`: Explicitly distinguishes `observed_fact`, `inference`, and `hypothesis` with supporting evidence linkages.

### Optimistic Concurrency Control
- `AnalysisSession`: Employs `version: int` column for optimistic locking to safeguard concurrent worker state updates without distributed locks.

---

## 2. Thin, Domain-Specific Repository Layer

* [packages/db/repositories/project_repo.py](file:///g:/RETRACE/packages/db/repositories/project_repo.py): Manages projects and application versions.
* [packages/db/repositories/analysis_repo.py](file:///g:/RETRACE/packages/db/repositories/analysis_repo.py): Manages analysis session lifecycle, optimistic status transitions (`ConcurrencyError`), and metrics.
* [packages/db/repositories/trajectory_repo.py](file:///g:/RETRACE/packages/db/repositories/trajectory_repo.py): Records actions and observations, reconstructs ordered trajectory timelines.
* [packages/db/repositories/finding_repo.py](file:///g:/RETRACE/packages/db/repositories/finding_repo.py): Manages findings, multi-attempt reproductions, root cause hypotheses, evidence, and derived reports.

---

## 3. Database Migration

* [migrations/versions/0002_harden_domain_and_persistence.py](file:///g:/RETRACE/migrations/versions/0002_harden_domain_and_persistence.py): Alembic migration defining:
  - `application_versions`, `trajectories`, `actions`, `observations`, `findings`, `evidence`, `reproduction_attempts`, `root_causes`, `reports`.
  - Cascading foreign keys (`ondelete="CASCADE"`), unique constraints, and indexes on high-frequency query paths.

---

## 4. Verification Results

| Suite / Check | Command | Result |
|---|---|---|
| Python Linting & Formatting | `ruff check .` | **PASS** (0 errors) |
| Backend Unit & Integration Tests | `pytest -v` | **PASS** (25/25 passed in 8.89s) |
| - Domain model invariants & sequence tests | `tests/unit/test_domain_models.py` | **PASS** (10 tests) |
| - Repository CRUD & optimistic locking tests | `tests/unit/test_repositories.py` | **PASS** (4 tests) |
| - Storage abstraction tests | `tests/unit/test_storage.py` | **PASS** (2 tests) |
| - Health & Readiness probes | `tests/integration/test_api_health.py` | **PASS** (3 tests) |
| - API v1 Projects & Analyses integration | `tests/integration/test_api_v1.py` | **PASS** (2 tests) |
| - Alembic Schema & FK constraint tests | `tests/integration/test_migrations.py` | **PASS** (2 tests) |
| Frontend Unit Tests | `cd apps/frontend && npm test -- --watch=false` | **PASS** (2 tests) |
| Frontend Production Build | `cd apps/frontend && npm run build` | **PASS** (0 errors, 270 kB bundle) |
