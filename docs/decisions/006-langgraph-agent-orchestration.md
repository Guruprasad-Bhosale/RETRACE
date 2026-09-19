# ADR 006: LangGraph & Provider-Agnostic LLM Interface

## Status
Accepted

## Context
AI reasoning is required to interpret differential findings, categorize anomalies, synthesize reproduction test logic, and correlate root causes with source code diffs.

## Decision
Use LangGraph for multi-step agent workflows combined with a provider abstraction layer (OpenAI, Anthropic, Gemini, local models).

## Rationale
* **Stateful Graph Workflows:** LangGraph enables explicit state transitions, cyclic reasoning loops, checkpointing, and deterministic branching based on tool outputs.
* **Provider Independence:** Encapsulating model invocations behind an interface prevents vendor lock-in and allows using cost-effective or self-hosted models for specific sub-tasks.
* **Structured Outputs:** Enforces typed Pydantic models for all LLM reasoning steps.

## Trade-offs
* Requires careful state schema versioning across long-running graph executions.
