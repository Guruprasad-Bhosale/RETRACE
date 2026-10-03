# RETRACE — PHASE 21: LANDING PAGE FOUNDATION
## Public Product Website + Entry Experience Completion Report

---

### 1. Landing Page Architecture

The RETRACE public-facing landing page is architecturally separated from the Command Center application. It introduces the product identity, engineering philosophy, and developer background using an **editorial / cinematic / personal / technical** aesthetic, while preserving the **forensic / data-dense / investigative** environment of the Command Center.

- **Component**: [`LandingPageComponent`](file:///g:/RETRACE/apps/frontend/src/app/pages/landing/landing.component.ts)
- **Styles**: [`landing.component.css`](file:///g:/RETRACE/apps/frontend/src/app/pages/landing/landing.component.css)
- **Template**: [`landing.component.html`](file:///g:/RETRACE/apps/frontend/src/app/pages/landing/landing.component.html)
- **Unit Spec**: [`landing.component.spec.ts`](file:///g:/RETRACE/apps/frontend/src/app/pages/landing/landing.component.spec.ts)

---

### 2. Route Structure

| Route | View | Description |
|---|---|---|
| `/` | **Public Landing Page** | High-level product introduction, mission, 4 pillars, forensic timeline, interactive visual specimen, developer profile, and project specs. |
| `/dashboard` | **Command Center Overview** | Live system telemetry, hero metrics, active investigations, and laboratory links. |
| `/projects` | **Project Laboratory** | Target repositories and workspace configurations. |
| `/analyses` | **Analyses State Machine** | Autonomous execution logs and multi-modal pipeline runs. |
| `/investigations` | **Forensic Case Index** | Case records, verification statuses, and causal summaries. |
| `/investigations/:id` | **Forensic Case File Deep-Dive** | Evidence DAG, A/B comparison slider, source diff attribution, and reproduction test script. |
| `/observability` | **Telemetry Hub** | Real-time streams, system metrics, and execution logs. |
| `/operations` | **Subsystem Topology** | Architecture health, service topology, and database state. |
| `/settings` | **Platform Settings** | API keys, workspace configurations, and telemetry options. |

---

### 3. Design Decisions

- **Visual Separation**: The Command Center's dense data rails and fixed status bars are hidden on `/`, allowing the landing page to render a full-width 12-column asymmetric editorial grid.
- **Editorial Typography**: Large geometric display typography (`Space Grotesk`, `Inter Tight`, `JetBrains Mono`) with clear typographic hierarchy (Display, Numeral, Heading, Body, Meta, Technical).
- **Restrained Palette**: Warm paper / obsidian foundation with `#FF5A1F` orange reserved strictly for interactive states, laser scan beams, active anchors, and causality nodes.
- **Zero Hallucinated Copy**: All marketing claims, statistics, developer biographies, and customer testimonials are structured as explicit, easily editable placeholder tokens (e.g. `[MISSION_HEADLINE]`, `[DEVELOPER_BIO]`, `[CORE_TECHNOLOGIES]`).

---

### 4. Sections Implemented

1. **Section 01 — Hero**:
   - High-contrast interactive `<app-tech-text>` canvas wordmark (`"RETRACE."` in `#FF5A1F`).
   - Oversized headline & supporting statement placeholders (`[HERO_OVERSIZED_HEADLINE]`, `[HERO_SUPPORTING_STATEMENT]`).
   - Primary `ENTER RETRACE` CTA and secondary `EXPLORE ARCHITECTURE ↓` anchor.
   - Right-side forensic metadata HUD card.
2. **Section 02 — Mission & Causality**:
   - Editorial section numeral (`02 // MISSION & CAUSALITY`).
   - Mission statement and explanation placeholders (`[MISSION_HEADLINE]`, `[MISSION_DESCRIPTION]`).
   - Deterministic causality flow: `VERSION A` $\to$ `BEHAVIOR` $\to$ `DIFFERENCE` $\to$ `EVIDENCE` $\to$ `ROOT CAUSE` $\to$ `VERSION B`.
3. **Section 03 — What is RETRACE (4 Editorial Pillars)**:
   - `OBSERVE`: Multi-modal capture (DOM, HAR, logs).
   - `COMPARE`: Behavioral alignment and divergence isolation.
   - `EXPLAIN`: Causal probabilistic DAG and source attribution.
   - `REPRODUCE`: Standalone test synthesis and offline snapshot replay.
4. **Section 04 — How RETRACE Works (Investigation Timeline)**:
   - 9-step interactive timeline with step selection inspector: `Version A`, `Observation`, `Evidence`, `Behavioral Difference`, `Hypothesis`, `Root Cause`, `Reproduction`, `Replay`, `Version B`.
5. **Section 05 — Forensic Visual Showcase**:
   - Interactive specimen canvas with tab switching (`EVIDENCE DAG`, `SOURCE DIFF`, `A/B REPLAY`).
   - Explicitly badged as `DEMONSTRATION SPECIMEN // SIMULATION ARTIFACT` to avoid confusion with live cases.
6. **Section 06 — The Developer**:
   - Personal editorial layout with portrait avatar slot (`[DEVELOPER_AVATAR_SLOT]`).
   - Placeholders for `[DEVELOPER_NAME]`, `[DEVELOPER_BIO]`, `[DEVELOPER_ENGINEERING_INTERESTS]`, `[DEVELOPER_PROJECT_MOTIVATION]`.
   - Channels for GitHub, LinkedIn, and Portfolio URLs.
7. **Section 07 — Project & Engineering Specs**:
   - Architecture philosophy and engineering principles placeholders (`[ARCHITECTURE_PHILOSOPHY]`, `[ENGINEERING_PRINCIPLES]`).
   - Technology stack specification (FastAPI, Python 3.12, PG16, Angular 19, Playwright).
   - Repository & documentation link slots.
8. **Section 08 — Final CTA & Entry Crossing**:
   - Grand `READY TO INVESTIGATE?` closing title with `[FINAL_CTA_SUPPORTING_STATEMENT]`.
   - `ENTER RETRACE COMMAND CENTER →` grand button.
   - Minimal editorial footer with back-to-top navigation and copyright metadata.

---

### 5. Motion Implemented

- **Landing $\to$ Command Center Transition**: Clicking `ENTER RETRACE` engages a 500ms high-tech laser scan curtain across the screen with HUD initialization text before navigating to `/dashboard`.
- **Reduced Motion Support**: Automatically detects `(prefers-reduced-motion: reduce)` and bypasses laser scan animations, navigating immediately to `/dashboard` with 0ms delay.
- **Micro-Interactions**: Hover elevation on workflow cards, smooth anchor scrolling across all sections, and interactive glyph tracking on the TechText canvas.

---

### 6. Responsive Behavior

- **Desktop ($1440\text{px}+, 1280\text{px}, 1024\text{px}$)**: Full 12-column asymmetric editorial layout with floating HUD metadata and side-by-side developer profile.
- **Tablet ($768\text{px}$)**: 2-column bento grids and compact timeline cards.
- **Mobile ($390\text{px}, 375\text{px}$)**: Responsive single-column vertical flow with dedicated mobile dropdown navigation and zero horizontal overflow.

---

### 7. Accessibility

- Semantic HTML5 section hierarchy (`<header>`, `<main>`, `<section>`, `<nav>`, `<footer>`).
- Headings (`<h1>`, `<h2>`, `<h3>`, `<h4>`) logically ordered across all 8 sections.
- Keyboard accessible navigation and visible focus rings (`outline: 2px solid var(--retrace-orange)`).
- Full `(prefers-reduced-motion: reduce)` respect.

---

### 8. Verification & Test Suite

- **Unit Tests**: **67 tests passing across 19 test files** (`npm test -- --watch=false`).
- **Production Build**: Clean compilation without errors in 2.68s (`npm run build`).

---

### 9. Files Changed

1. `apps/frontend/src/app/pages/landing/landing.component.ts` (New component logic & workflow signals)
2. `apps/frontend/src/app/pages/landing/landing.component.html` (8 editorial sections & placeholder tokens)
3. `apps/frontend/src/app/pages/landing/landing.component.css` (Editorial grid, dividers, and laser scan curtain)
4. `apps/frontend/src/app/pages/landing/landing.component.spec.ts` (Unit test coverage for landing page)
5. `apps/frontend/src/app/app.routes.ts` (Mounted `/` to LandingPageComponent, preserved `/dashboard`)
6. `apps/frontend/src/app/app.ts` & `app.html` (Separated Command Center shell from Landing Page canvas)
7. `apps/frontend/src/app/app.spec.ts` (Updated route navigation unit tests)

---

### 10. Content Placeholders Requiring User Input

| Section | Placeholder Token | Content to Supply |
|---|---|---|
| **01 Hero** | `[HERO_OVERSIZED_HEADLINE]` | Primary marketing hero headline |
| **01 Hero** | `[HERO_SUPPORTING_STATEMENT]` | 1-2 sentence platform introduction |
| **02 Mission** | `[MISSION_HEADLINE]` | Core problem statement |
| **02 Mission** | `[MISSION_DESCRIPTION]` | Mission narrative / philosophy |
| **03 Pillars** | `[OBSERVE_SUMMARY_PLACEHOLDER]` | Observation pillar summary |
| **03 Pillars** | `[COMPARE_SUMMARY_PLACEHOLDER]` | Comparison pillar summary |
| **03 Pillars** | `[EXPLAIN_SUMMARY_PLACEHOLDER]` | Causal explanation summary |
| **03 Pillars** | `[REPRODUCE_SUMMARY_PLACEHOLDER]` | Reproduction test summary |
| **06 Developer** | `[DEVELOPER_AVATAR_SLOT]` | Portrait photo / SVG illustration |
| **06 Developer** | `[DEVELOPER_NAME]` | Creator / Engineer Name |
| **06 Developer** | `[DEVELOPER_BIO]` | Professional engineering bio |
| **06 Developer** | `[DEVELOPER_ENGINEERING_INTERESTS]` | Technical focus areas |
| **06 Developer** | `[DEVELOPER_PROJECT_MOTIVATION]` | Motivation behind building RETRACE |
| **06 Developer** | `[DEVELOPER_GITHUB_URL]` | Personal GitHub link |
| **06 Developer** | `[DEVELOPER_LINKEDIN_URL]` | Personal LinkedIn link |
| **06 Developer** | `[DEVELOPER_PORTFOLIO_URL]` | Personal portfolio / site link |
| **07 Project** | `[ARCHITECTURE_PHILOSOPHY]` | Architecture summary |
| **07 Project** | `[REPOSITORY_URL]` | Public repository URL |
| **07 Project** | `[DOCS_URL]` | Public documentation URL |
| **08 Final CTA** | `[FINAL_CTA_SUPPORTING_STATEMENT]` | Closing call-to-action text |

---

### 11. Known Limitations

- All copy and biographical data are currently tokens awaiting your input before production release.
- Visual specimens are intentionally labeled as demonstration specimens rather than querying live investigation runs.
