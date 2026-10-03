# INVESTIGATION REPLAY & DETERMINISM ARCHITECTURE 2.0

## 1. Executive Summary

Investigation Replay in RETRACE provides a deterministic, offline verification capability that re-executes forensic reasoning from immutable captured snapshots without invoking browser automation, making outbound network requests, querying Git repositories, or mutating persistent storage.

```text
SNAPSHOT
   ↓
EVIDENCE
   ↓
GRAPH TOPOLOGY
   ↓
HYPOTHESIS GENERATION
   ↓
EVIDENCE CORRELATION
   ↓
ELIMINATION
   ↓
FALSIFICATION
   ↓
ROOT CAUSE
   ↓
CANONICAL HASH VERIFICATION
```

---

## 2. Replay Snapshots & Canonical Hashing

An `InvestigationReplaySnapshot` captures the immutable inputs of an investigation:
- `investigation_id`: Stable identifier
- `schema_version`: Schema standard (e.g. `v1`)
- `analysis_version`: Forensic engine algorithm version (e.g. `forensics-v1`)
- `snapshot_hash`: Canonical SHA-256 hash computed using deterministic JSON normalization (sorting keys, stripping transient timestamps)
- `evidence_items`, `observations`, `diffs`, `hypotheses`, `source_references`, `reproduction_results`, and `deterministic_config`.

### Canonical Hash Derivations
- **Graph Topology Hash (`graph_hash`)**: Computed over deterministically sorted nodes (`node_id`, `node_type`, `title`, `status`, `evidence_item_ids`) and sorted edges (`edge_id`, `source_node_id`, `target_node_id`, `relationship`).
- **Hypothesis Set Hash (`hypothesis_hash`)**: Computed over sorted hypotheses (`hypothesis_id`, `category`, `status`, `supporting_evidence_ids`, `contradicting_evidence_ids`, `elimination_reason`).
- **Explanation Hash (`explanation_hash`)**: Computed over `(investigation_id, root_cause_summary, root_cause_status, primary_hypothesis_id, primary_hypothesis_status, confidence_level, confidence_score, falsification_statement, provenance)`.

---

## 3. Replay Verification Workflow

When `POST /api/v1/investigations/{id}/replay` is invoked:
1. An immutable snapshot is captured or retrieved.
2. The `ForensicIntelligenceEngine` reconstructs the explanation and evidence graph entirely in memory.
3. The replayed hashes are compared against the baseline hashes.
4. If identical: `status = "REPRODUCIBLE"`, `is_reproducible = True`.
5. If divergent: `status = "DIVERGENCE_DETECTED"`, `is_reproducible = False`, with exact divergence items enumerated.

---

## 4. Multi-Investigation Comparison

The `compare_investigations` service computes structural and topological differences between two investigations:
- Identifies shared vs unique evidence items.
- Detects graph diff operations: `ADDED_NODE`, `REMOVED_NODE`, `CHANGED_EDGE`, `CHANGED_STATE`, and `CHANGED_ROOT_CAUSE`.
- Exposes divergences in root cause summaries and falsification conditions.
