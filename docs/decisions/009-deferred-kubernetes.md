# ADR 009: Intentional Deferral of Kubernetes

## Status
Accepted

## Context
Deploying and managing Kubernetes clusters adds significant operational overhead (Helm charts, ingress controllers, RBAC, storage drivers) during the initial architecture and validation phases.

## Decision
Target Docker Compose for local development and containerized serverless / task runtimes (e.g. AWS ECS/Fargate) for initial cloud deployment. Defer Kubernetes until horizontal multi-cluster scaling is specifically required.

## Rationale
* **Focus on Product Engineering:** Engineering efforts in initial phases should prioritize exploration quality, regression classification accuracy, and root cause precision rather than cluster management.
* **Docker Portability:** Well-designed container images and stateless services run seamlessly on Docker Compose, ECS, or Kubernetes without rewriting application logic.

## Trade-offs
* Advanced Kubernetes-specific CRDs or service mesh features are not utilized initially.
