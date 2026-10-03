# EVIDENCE GRAPH ARCHITECTURE 2.0

## 1. Executive Summary

The Evidence Graph in RETRACE represents a deterministic, auditable Directed Acyclic Graph (DAG) that establishes causal provenance between initial runtime observations and localized root-cause source code modifications.

```text
                  ┌──────────────┐
                  │ OBSERVATION  │
                  └──────┬───────┘
                         │
                         ▼
                ┌─────────────────┐
                │ BEHAVIOR CHANGE │
                └────────┬────────┘
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
         DOM DIFF    NETWORK DIFF  STATE DIFF
             │           │           │
             └───────────┼───────────┘
                         ▼
                 ┌──────────────┐
                 │ HYPOTHESIS   │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ SOURCE DIFF  │
                 └──────┬───────┘
                        │
                        ▼
                  ┌────────────┐
                  │ ROOT CAUSE │
                  └─────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │ REPRODUCTION│
                 └─────────────┘
```

---

## 2. Core Graph Data Structures

The evidence graph model is defined in [packages/forensics/models.py](file:///g:/RETRACE/packages/forensics/models.py) using strict Pydantic schemas:

### Node Specification
- `node_id`: Deterministic hash derived from entity type and primary identifiers (e.g. `diff_nav_001`, `hyp_0`).
- `node_type`: Strongly-typed enum (`OBSERVATION`, `SEMANTIC_DIFF`, `HYPOTHESIS`, `AST_DIFF`, `REPRODUCTION`, `ROOT_CAUSE`).
- `label`: Concise, editorial label for visual rendering.
- `status`: Verification lifecycle state (`OBSERVED`, `PROPOSED`, `SUPPORTED`, `CONFIRMED`, `ELIMINATED`, `WEAKENED`, `REPRODUCED`).
- `confidence`: Optional float score [0.0 - 1.0].
- `metadata`: Key-value attributes preserving source file paths, line numbers, commit SHAs, and selector tags.

### Edge Specification
- `edge_id`: Deterministic ID (`edge_{source_id}_{target_id}_{relationship}`).
- `source_id`: Originating node identifier.
- `target_id`: Terminating node identifier.
- `relationship`: Explicit semantic relationship:
  - `DERIVED_FROM`: Semantic difference derived from trace observations.
  - `SUPPORTS`: Observation or diff supporting a hypothesis.
  - `CONTRADICTS`: Observation or diff falsifying a hypothesis.
  - `CAUSED_BY`: Regression finding linked to AST source modifications.
  - `CORRELATES_WITH`: Association between parallel runtime events.
  - `REPRODUCES`: Deterministic Playwright script reproducing the failure.
  - `LOCATED_AT`: Root cause pinpointed to file and line range.
  - `INVALIDATES`: Counter-evidence eliminating candidate hypotheses.
- `weight`: Strength of relationship based on forensic weighting rubric.

---

## 3. Graph Construction Protocol

The `EvidenceGraphBuilder` in [packages/forensics/graph_builder.py](file:///g:/RETRACE/packages/forensics/graph_builder.py) follows an exact deterministic order:

1. **Root Observation**: Emits `obs_root` capturing the initial trajectory anomaly.
2. **Behavioral Diffs**: Iterates over `differences` in `SemanticDiffResult`, emitting `diff_{diff_id}` nodes with `DERIVED_FROM` edges to `obs_root`.
3. **Primary Hypothesis**: Generates `hyp_0` with `SUPPORTS` edges from all correlated diffs.
4. **AST / Source Modification**: If `RootCauseResult` is present, emits `src_{file}_{start_line}` with `LOCATED_AT` edge from the hypothesis.
5. **Reproduction Node**: Emits `rep_{id}` with `REPRODUCES` edge linked to the regression hypothesis.
6. **Root Cause Synthesis**: Emits `rc_{finding_id}` with `CAUSED_BY` edge to the AST source location.

---

## 4. Multi-Tenant Isolation & Storage

Evidence graphs are completely isolated by tenant context:
- Every graph node and edge is generated within the scope of an `InvestigationResult`.
- API endpoints enforce Organization ID and Workspace ID matching via session claims.
- Cross-tenant lookups fail closed with HTTP 404/403.
