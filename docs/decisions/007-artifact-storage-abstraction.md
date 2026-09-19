# ADR 007: Pluggable Artifact Storage Abstraction (MinIO / S3 / Local)

## Status
Accepted

## Context
Investigation runs generate heavy binary and text artifacts: screenshots, DOM dumps, HAR network recordings, Playwright trace archives, and generated reproduction scripts.

## Decision
Introduce an abstract `ArtifactStorage` interface with pluggable `LocalDiskArtifactStorage` (for local development and testing) and `S3ArtifactStorage` (for MinIO and AWS S3).

## Rationale
* **Zero Cloud Coupling in Core Engine:** Domain and worker logic store artifacts using storage keys/URIs without coupling to boto3 or minio SDK APIs directly.
* **Fast Local Development:** Enables running tests and local explorations without launching MinIO or AWS services.
* **Cost & Scale:** Large blobs remain in object storage rather than bloating the PostgreSQL database.

## Trade-offs
* Requires managing lifecycle policies for temporary and retained artifacts.
