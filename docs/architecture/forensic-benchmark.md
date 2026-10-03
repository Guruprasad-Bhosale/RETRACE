# FORENSIC BENCHMARK & EVALUATION DATASET 2.0

## 1. Overview & Oracle Isolation

The Dedicated Forensic Benchmark Dataset (`tests/fixtures/forensics/forensic_cases.json`) evaluates the reasoning, elimination, and falsification capabilities of RETRACE without leaking ground truth into the production analysis pipeline.

```text
                    ┌───────────────┐
                    │ GROUND TRUTH  │ (Evaluator-Only)
                    └───────┬───────┘
                            │
                       EVALUATION
                            │
                            ▼
┌───────────────┐     ┌──────────────┐
│ RETRACE       │ ──→ │ COMPARATOR   │
│ INFERENCE     │     │              │
└───────────────┘     └──────────────┘
```

---

## 2. Benchmark Case Taxonomy (Cases A - J)

| Case ID | Scenario | Expected Outcome |
|---|---|---|
| **CASE_A_DIRECT_SOURCE** | Direct calculation logic bug with AST & reproduction | `CALCULATION_LOGIC` hypothesis `CONFIRMED` |
| **CASE_B_PRESENTATION_ONLY** | Visual CSS button styling difference | `STYLING_FORMATTING` `SUPPORTED`, no false calculation root cause |
| **CASE_C_NETWORK_REGRESSION** | Backend API 500 endpoint failure | `API_CONTRACT` hypothesis `CONFIRMED` |
| **CASE_D_TIMING_FLAKINESS** | Intermittent race condition during hydration | `TIMING_RACE_CONDITION` `SUPPORTED` |
| **CASE_E_MULTIPLE_PLAUSIBLE** | Tax calculation vs formatting ambiguity | `CALCULATION_LOGIC` `CONFIRMED`, `STYLING` `ELIMINATED` |
| **CASE_F_MISSING_EVIDENCE** | Anomaly with no source or reproduction | `UNKNOWN` hypothesis `PROPOSED` (Unresolved) |
| **CASE_G_CONTRADICTORY** | Conflicting HTTP 200 vs console exception | Contradiction surfaced in graph & hypothesis |
| **CASE_H_FALSE_CORRELATION** | Unrelated documentation commit nearby | `CAUSED_BY` edge rejected |
| **CASE_I_REPRODUCTION_FAILURE** | Candidate identified but automated replay fails | Hypothesis status set to `WEAKENED` |
| **CASE_J_ADVERSARIAL_EVIDENCE** | Prompt injection payload inside observed DOM text | Injection neutralized; prompt safety preserved |

---

## 3. Evaluation Metrics

- **Hypothesis Precision & Recall**: Verifies correct hypothesis category assignment and lifecycle status.
- **Root-Cause Localization**: Pinpoints exact source files and line ranges.
- **Evidence & Provenance Coverage**: Evaluates that 100% of factual assertions reference authoritative evidence items in the graph catalog.
- **Unsupported Claim Detection**: Flags any ungrounded assertions.
