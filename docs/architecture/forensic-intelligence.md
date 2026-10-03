# FORENSIC INTELLIGENCE ARCHITECTURE 2.0

## 1. Principles of Forensic Truth

RETRACE implements a strict forensic hierarchy where deterministic observation always supersedes probabilistic interpretation:

```text
OBSERVED SYSTEM EVIDENCE
        ↓
DETERMINISTIC ANALYSIS
        ↓
EVIDENCE CORRELATION
        ↓
INTELLIGENCE / INTERPRETATION
```

### Absolute Constraints
1. **No Hallucinated Evidence**: The engine never generates fictional DOM nodes, network payloads, or Git commits.
2. **Fail-Closed Validation**: Any reference to a non-existent evidence ID raises an `InvalidEvidenceReferenceError` and halts synthesis.
3. **Transparent Weighting**: Confidence scores are mathematically derived from verified artifacts (+0.40 reproduction, +0.35 AST source correlation, +0.20 deterministic diffs).
4. **Adversarial Prompt Defense**: Observed page content, DOM text, console logs, and commit messages are scrubbed for instruction injection patterns (`IGNORE PREVIOUS`, `SYSTEM OVERRIDE`, etc.).

---

## 2. Hypothesis Engine & Elimination Logic

The `HypothesisEngine` ([packages/forensics/hypothesis_engine.py](file:///g:/RETRACE/packages/forensics/hypothesis_engine.py)) evaluates competing explanations for observed regression behavior:

### Lifecycle States
- `PROPOSED`: Initial candidate formulation.
- `SUPPORTED`: Accumulated supporting diffs and telemetry.
- `WEAKENED`: Evidence contradicts without full refutation.
- `ELIMINATED`: Definitive counter-evidence rules out the hypothesis.
- `CONFIRMED`: Reproduction succeeded and source correlation established.
- `UNRESOLVED`: Insufficient telemetry to confirm or refute.

### Standard Alternatives Evaluated & Rule-Out Criteria
1. **DOM Structure / Presentation Only**: Eliminated if network payload or application calculation changed.
2. **Network / Backend Outage**: Eliminated if network HTTP status codes are 200/201 and payload schema unchanged.
3. **Timing / Flakiness**: Eliminated if reproduction script executes deterministically across consecutive runs.

---

## 3. Falsification Framework

Every confirmed root cause exposes explicit falsification criteria ([packages/forensics/falsification.py](file:///g:/RETRACE/packages/forensics/falsification.py)):
- **Condition**: A testable counter-scenario (e.g. *"If reverting commit X still produces mismatch Y on version B, the conclusion is falsified"*).
- **Test Scenario**: Concrete automated test script or manual verification step.
- **Potential Confounders**: Identified variables such as caching, third-party CDNs, or volatile timestamps.

---

## 4. API Endpoints

- `GET /api/v1/investigations/{id}/evidence-graph`: Returns the complete DAG nodes, edges, and provenance metadata.
- `GET /api/v1/investigations/{id}/explanation`: Returns the structured forensic explanation including primary hypothesis, confidence metrics, eliminated alternatives, and falsification conditions.
