# ADR 003: PostgreSQL with pgvector for Relational and Semantic Storage

## Status
Accepted

## Context
RETRACE manages structured relational entities (Projects, Analysis Sessions, Findings, Evidence, Reproductions) and will later index source code chunks and error logs with semantic embeddings.

## Decision
Use PostgreSQL 16+ with the `pgvector` extension as the primary database.

## Rationale
* **ACID Guarantees:** Relational integrity for analysis runs, state graphs, and evidence links.
* **Unified Database Engine:** `pgvector` allows vector similarity search directly in PostgreSQL without requiring a separate vector database (e.g. Pinecone, Milvus, Chroma).
* **JSONB Capabilities:** Native JSONB support enables flexible storage of dynamic DOM structures and network payloads.

## Trade-offs
* Requires database migration discipline (managed via Alembic).
