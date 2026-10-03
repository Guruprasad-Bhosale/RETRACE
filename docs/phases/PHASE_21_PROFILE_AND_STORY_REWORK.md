# RETRACE — PHASE 21: PROFILE CARD & FORENSIC STORY REWORK
**Minimal • Spacious • Story-Driven • Smooth**

---

## 1. Profile Card Changes & Noise Removal

The developer profile card has been refined to put full focus on the builder, eliminating all decorative clutter and dashboard metadata:

- **Removed Clutter**:
  - Removed `HUMAN_OPERATOR // 01` tag.
  - Removed `RETRACE CORE` label.
  - Removed `Building RETRACE` status pill.
  - Removed rainbow holographic gradients and excessive 3D distortion.
- **Retained Core Elements**:
  - Large portrait image: `snf.jpg` occupying ~60–70% of card height with generous `rounded-[20px]`.
  - Identity: **Guruprasad Bhosale** (prominent, bold).
  - Title: `BUILDER OF RETRACE.` (technical monospace uppercase).
  - Handle: `@guruprasad-bhosale` (muted monospace).
  - Clean text links: `GITHUB ↗` and `LINKEDIN ↗`.

---

## 2. The Two Selected Card Visual Effects

### Effect 01: Behind Glow
- Soft RETRACE orange (`rgba(255, 90, 31, 0.22)`) radial light source positioned **behind** the card (`z-0`, `blur-2xl`).
- Coordinates smoothly track the pointer via `requestAnimationFrame` with linear interpolation.
- Fades in upon entering the card and gently fades out upon leaving without causing Angular change detection cycles.

### Effect 02: Forensic Icon / Particle Pattern
- Very subtle geometric texture (forensic crosshairs `+`, micro-dots, coordinate nodes) embedded inside the card background (`opacity: 0.15`, increases to `0.30` on hover).
- Subtly shifts with pointer coordinates ($\pm 6\text{px}$) to provide depth without distracting from the photograph.

---

## 3. Forensic Trajectory Redesign

The Hero Trajectory panel was redesigned from a boxed dashboard widget into an editorial **vertical visual timeline**:
- **Continuous Gradient Spine**: Vertical line connecting all stages from `VERSION A` (green baseline) through `OBSERVE`, `DIFFERENCE`, `EVIDENCE`, `ROOT CAUSE` to `VERSION B` (rose defect).
- **Minimal Nodes & Stage Descriptors**:
  1. `01 VERSION A` &bull; *Baseline*
  2. `02 OBSERVE` &bull; *Runtime behavior*
  3. `03 DIFFERENCE` &bull; *Behavioral delta*
  4. `04 EVIDENCE` &bull; *Causal proof*
  5. `05 ROOT CAUSE` &bull; *Source change*
  6. `06 VERSION B` &bull; *Explained*
- **Subtle Hover State**: Hovering any stage highlights the active stage while keeping the connecting line intact.

---

## 4. Story-Driven Narrative Transitions

Subtle transition markers link each chapter into a continuous story:

```
01 — HERO (What is RETRACE?)
      ↓  "SCROLL TO TRACE THE STORY ↓"
02 — MISSION (Why does it exist?)
      ↓  "FROM CAUSE TO REPRODUCTION ↓"
03 — HOW IT WORKS (How does it investigate?)
      ↓  "SOMEONE HAD TO BUILD THE SYSTEM ↓"
04 — THE DEVELOPER (Who built it?)
      ↓  "THE SYSTEM IS READY ↓"
05 — ACCESS RETRACE (Enter the system)
```

---

## 5. Responsive Verification & Accessibility

- **Desktop**: 12-column layout with 5-column profile card and 7-column editorial story.
- **Mobile**: Full-width card with comfortable horizontal padding and clean stacked links.
- **Accessibility**:
  - Full keyboard navigation for all links and actions.
  - Automatic disablement of behind glow, particle shifts, and animations when `prefers-reduced-motion: reduce` is active.

---

## 6. Automated Tests & Production Build

- **Unit Tests**:
  - `DeveloperProfileCardComponent` test suite (6 tests passed).
  - `LandingPageComponent` test suite (7 tests passed).
  - Total: **20 test files, 76/76 unit tests passed** (`npm test -- --watch=false`).
- **Production Build**: `ng build` succeeded with **0 errors**.

---

## 7. Files Changed

| File | Type | Description |
| :--- | :--- | :--- |
| `apps/frontend/src/app/shared/components/developer-profile-card/developer-profile-card.component.ts` | Logic | Cleaned up properties; added Behind Glow and Icon Pattern shift handlers. |
| `apps/frontend/src/app/shared/components/developer-profile-card/developer-profile-card.component.html` | Template | Implemented Behind Glow, forensic particle pattern, and clean identity layout. |
| `apps/frontend/src/app/shared/components/developer-profile-card/developer-profile-card.component.css` | Styles | Cleaned up CSS with reduced motion overrides. |
| `apps/frontend/src/app/shared/components/developer-profile-card/developer-profile-card.component.spec.ts` | Tests | Unit tests verifying Behind Glow and links. |
| `apps/frontend/src/app/pages/landing/landing.component.html` | Template | Integrated story-driven narrative transitions and updated forensic trajectory. |
| `apps/frontend/src/app/pages/landing/landing.component.ts` | Logic | Added trajectory hover states and stage descriptors. |
| `docs/phases/PHASE_21_PROFILE_AND_STORY_REWORK.md` | Docs | Release documentation. |

---

## 8. Remaining Issues
None. The landing page is completely functional, minimal, story-driven, tested, and running locally.
