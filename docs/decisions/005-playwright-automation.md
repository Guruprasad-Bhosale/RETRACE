# ADR 005: Playwright for Browser Observation & Reproduction

## Status
Accepted

## Context
The platform requires deep browser introspection (DOM mutations, CDP network events, console logs, accessibility tree snapshots, screenshots, action execution) and must generate self-contained, reproducible tests.

## Decision
Adopt Microsoft Playwright with Chromium as the core browser automation engine.

## Rationale
* **Deep Chrome DevTools Protocol (CDP) Integration:** Enables capturing raw HAR network logs, console streams, and accessibility trees synchronously.
* **Auto-Waiting & Reliability:** Minimizes flaky interactions during autonomous exploration.
* **Industry Standard Test Artifact:** Generated Playwright Python/TypeScript reproduction scripts can be executed directly in CI pipelines by engineering teams.

## Trade-offs
* Browser binaries have a larger disk and memory footprint during worker container execution.
