# ADR 008: Modular Monolith Architecture First

## Status
Accepted

## Context
Prematurely splitting an evolving system into dozens of microservices adds network latency, deployment complexity, distributed transaction overhead, and difficult debugging.

## Decision
Structure RETRACE as a modular monorepo (`apps/api`, `apps/worker`, `apps/frontend`, `packages/*`) with clear dependency boundaries and domain isolation.

## Rationale
* **Rapid Iteration with Strong Boundaries:** Code refactoring and contract evolution can happen safely within a single repository without version skew across repositories.
* **Extraction Readiness:** Because packages (`domain`, `storage`, `db`, `redis_client`, `logging`) and apps (`api`, `worker`) have zero circular dependencies, any engine service (e.g. explorer, diff-engine, reproducer) can be extracted into an independent microservice in the future if scale demands it.

## Trade-offs
* Requires strict linting and architectural discipline to prevent boundary leakage.
