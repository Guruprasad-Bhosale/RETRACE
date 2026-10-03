# RETRACE Forensic Motion & Interaction Architecture 2.0

## Overview & Mission

Phase 19B elevates the RETRACE frontend from a static visual layout into an **interactive forensic instrument**.
The system communicates causality, state progression, and empirical relationships through coordinated interaction and motion.

The central forensic progression is:
```text
OBSERVATION
      ↓
EVIDENCE
      ↓
HYPOTHESIS
      ↓
SOURCE
      ↓
REPRODUCTION
      ↓
ROOT CAUSE
```

---

## 1. Centralized Motion Architecture

All motion tokens and transitions are strictly centralized in [styles.css](file:///g:/RETRACE/apps/frontend/src/styles.css) without scattered ad-hoc CSS transitions.

### 1.1 Motion Tokens

```css
--ease-retrace: cubic-bezier(.22, 1, .36, 1);
--duration-fast: 180ms;
--duration-normal: 400ms;
--duration-slow: 600ms;
--duration-reveal: 800ms;
```

### 1.2 Reusable Motion Classes & Keyframes

| Utility Class | Purpose | Transition & Easing |
| :--- | :--- | :--- |
| `.page-enter` | Content entry on route change without shell shift | `opacity`, `translateY(12px) → 0` in 600ms |
| `.fade-up` | Subsystem card appearance | `opacity`, `translateY(16px) → 0` in 400ms |
| `.clip-reveal` | Heading and metadata unmasking | `clip-path: inset(0 100% 0 0)` in 600ms |
| `.scale-in` | Node and badge reveal | `transform: scale(0.96) → 1` in 400ms |
| `.line-draw` | SVG edge path initial draw | `stroke-dashoffset: 1000 → 0` in 800ms |
| `.forensic-path` | Active causal trajectory stream | Linear animated dash flow (`6px 4px`) |
| `.forensic-pulse`| Orange relationship accentuation | 2s restrained glow breathing |
| `.sweep-highlight`| Source line background sweep | 1.2s single background emphasis |
| `.forensic-scanner`| Multi-stage scan beam for loading | 1.8s horizontal scan gradient |
| `.error-state-pulse`| Single border error alert | 0.8s single pulse, remaining static |

---

## 2. Bento Interaction Families

Standardized across all views:

- **Family A (`.bento-lift`)**: Hover translation `translateY(-3px)` with subtle orange shadow.
- **Family B (`.bento-meta-shift`)**: Internal metadata indicator translation `translateX(3px)` with orange text accent.
- **Family C (`.bento-reveal`)**: Vertical 3px orange border unmasking upon hover/selection.

---

## 3. Coordinated Forensic Synchronization

State coordination is handled by the reactive [ForensicInteractionService](file:///g:/RETRACE/apps/frontend/src/app/core/services/forensic-interaction.service.ts).

```text
[ EVIDENCE GRAPH NODE ] ──── (select) ───► [ ForensicInteractionService ]
                                                    │
         ┌──────────────────┬───────────────────────┼──────────────────────┬─────────────────┐
         ▼                  ▼                       ▼                      ▼                 ▼
[ Connected Nodes ]  [ Connected Edges ]  [ Hypothesis Card ]  [ Source Diff Line ]  [ Root Cause Chain ]
 (Highlight & Glow)   (Animated Dash)      (Orange Accent)       (Sweep Highlight)    (Step Accentuation)
```

### 3.1 Interaction Rules:
1. **Evidence Node Selected / Hovered**:
   - Selected node scales `1.04`, receives orange ring.
   - Connected nodes stay prominent.
   - Unrelated nodes dim to opacity `0.35`.
   - Connected edges highlight in orange with animated line dash.
2. **Hypothesis Synchronized**:
   - Related hypothesis receives orange emphasis with textual status badges (`CONFIRMED`, `SUPPORTED`, `PROPOSED`, `ELIMINATED`, `CONFLICTED`).
3. **Source Synchronized**:
   - Code viewer targets attributed file and start line with single sweep highlight.
4. **Follow Evidence Playback (`FOLLOW EVIDENCE →`)**:
   - Visual playback sequencer moving sequentially through `OBSERVE → DIFF → HYPOTHESIZE → SOURCE → REPRODUCTION → ROOT CAUSE`.
   - Playback controls: `PLAY`, `PAUSE`, `RESUME`, `SKIP`, `EXIT`, `1×/2×`.

---

## 4. Responsive & Mobile Strategy

- **Desktop (>= 1024px)**: Full 2D DAG flow with connected edge table and dual-column Bento workstation.
- **Tablet (640px - 1023px)**: Compressed responsive 3-column DAG grid.
- **Mobile (< 640px)**: Dedicated vertical linear chain:
  `OBSERVATION ↓ DIFF ↓ HYPOTHESIS ↓ SOURCE ↓ ROOT CAUSE`
  Mobile workstation order: Header → Timeline → Root Cause → Evidence → Hypotheses → Source → Reproduction.

---

## 5. Accessibility & Reduced Motion

- **Keyboard Navigation**:
  - Full `Tab` and `Shift+Tab` flow.
  - Arrow key navigation (`ArrowLeft`, `ArrowRight`, `ArrowUp`, `ArrowDown`) inside Evidence Graph.
  - `Enter` / `Space` to select, `Escape` to clear selection and close overlays.
  - Focus ring: `outline: 2px solid var(--retrace-orange); outline-offset: 3px;`.
- **Reduced Motion (`prefers-reduced-motion: reduce`)**:
  - Automatically disables ambient cursor glow, animations, sweep highlights, and scan beams.
  - Transitions to instantaneous deterministic state changes.
