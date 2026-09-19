# ADR 002: Python 3.12+ & FastAPI for Backend Services

## Status
Accepted

## Context
The backend must handle high-throughput async I/O, coordinate browser workers, interface with AI agent workflows, and serve structured OpenAPI REST contracts.

## Decision
Use Python 3.12+ with FastAPI, Pydantic v2, and SQLAlchemy 2.0.

## Rationale
* **Native AI Ecosystem:** Python provides first-class support for LLM orchestration frameworks (LangGraph, LangChain), AST parsers, and tokenizers.
* **Asynchronous Performance:** FastAPI on uvloop/asyncio delivers high concurrent request throughput.
* **Pydantic v2:** Rust-backed validation core provides type validation and automatic OpenAPI documentation.

## Trade-offs
* Python global interpreter lock (GIL) requires multi-process worker pools for CPU-intensive tasks (e.g. AST diffing and visual comparison).
