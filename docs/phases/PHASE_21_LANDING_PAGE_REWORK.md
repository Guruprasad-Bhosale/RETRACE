# RETRACE — PHASE 21: LANDING PAGE 2.0
**Full-Width • Editorial • Story-Driven • Spacious • Minimal**

---

## 1. Existing Landing Page Problems Diagnosed

- **Artificial Containment**: Content was boxed inside a narrow `max-w-6xl` container, creating small cards on a vast black background rather than an expansive editorial composition.
- **100% Browser Zoom Issues**: At standard desktop viewports (1792×855, 1920×1080), the previous layout left unutilized horizontal margins and cramped visual elements.
- **Small Dashboard Trajectory**: The forensic trajectory visual was constrained inside a tiny card rather than commanding its rightful place as a substantial visual instrument.

---

## 2. New Page Composition & Story Architecture

The entire landing page now functions as a unified narrative spanning the full viewport width:

```
01 // HERO (What is RETRACE?)
     - Full-width 12-column layout (Left 7 cols: Eyebrow + TechText Wordmark + Headline + Supporting Narrative + CTAs)
     - Right 5 cols: Large Forensic Trajectory Timeline (Version A → Observe → Difference → Evidence → Root Cause → Version B)
     ↓
STORY TRANSITION: FULL-WIDTH TEXTLOOP
     - Continuous SVG wave path: "TRACE ✦ OBSERVE ✦ COMPARE ✦ EVIDENCE ✦ ROOT CAUSE ✦ REPRODUCE"
     ↓
02 // MISSION (Why does it exist?)
     - Eliminating guesswork from regression diagnosis.
     - Wide horizontal 6-stage causal flow spanning full available width.
     ↓
03 // HOW IT WORKS (How does it investigate?)
     - Four spacious editorial pillar blocks: Observe, Compare, Explain, Reproduce.
     ↓
04 // THE INVESTIGATION (How does it prove the cause?)
     - "A regression is not a guess. It is a trail."
     - 70/30 interactive forensic breakdown connecting runtime behavior to causal evidence.
     ↓
05 // THE DEVELOPER (Who built it?)
     - Left (45%): Large Developer Profile Card (snf.jpg, Behind Glow, Icon/Particle Pattern).
     - Right (55%): "Built by curiosity. Shaped by engineering." + Bio + Verified Channels.
     ↓
06 // ACCESS RETRACE & MINIMAL FOOTER
     - "READY TO INVESTIGATE?" + [ ENTER RETRACE → ] + Minimal 1-row Footer.
```

---

## 3. Full-Width Layout Strategy

- **Global Container Width**: Configured as `max-w-[1720px] w-[min(100%-2rem,1720px)] sm:w-[min(100%-4rem,1720px)] lg:w-[min(100%-6rem,1720px)] mx-auto`.
- **Viewport Utilization**: Content utilizes 88–94% of horizontal width across 1440px–1920px viewports with generous fluid typography (`clamp()`).
- **No Unnecessary Boxes**: Sections flow naturally with editorial horizontal rules and orange registration marks.

---

## 4. TextLoop Component (Native Angular + GSAP)

- **Component**: [`TextLoopComponent`](file:///g:/RETRACE/apps/frontend/src/app/shared/components/text-loop/text-loop.component.ts)
- **Engine**: Pure Angular + SVG `<textPath>` + GSAP for continuous, stutter-free wrapping.
- **Palette**: Warm off-white text (`var(--ink)`), RETRACE orange separator (`#FF5A1F`), subtle dark ribbon.
- **Accessibility & Motion**: Automatically pauses on hover (`pauseOnHover`), disables GSAP animation when `prefers-reduced-motion` is active, and cleans up timelines on `ngOnDestroy`.

---

## 5. Developer Section: Native 3D Profile Card

- **Component**: [`DeveloperProfileCardComponent`](file:///g:/RETRACE/apps/frontend/src/app/shared/components/developer-profile-card/developer-profile-card.component.ts)
- **Effects**:
  1. **Behind Glow**: Soft RETRACE orange (`rgba(255, 90, 31, 0.22)`) radial light following cursor smoothly via `requestAnimationFrame`.
  2. **Forensic Icon / Particle Pattern**: Subtle geometric SVG crosshair & node texture that subtly shifts with pointer movement.
- **Asset**: Real portrait image [`snf.jpg`](file:///g:/RETRACE/apps/frontend/public/snf.jpg).
- **Verified Links**: [GitHub ↗](https://github.com/Guruprasad-Bhosale) and [LinkedIn ↗](https://www.linkedin.com/in/guruprasad-bhosale).

---

## 6. Responsive Viewport QA Matrix

| Viewport | Status | Layout Behavior |
| :--- | :--- | :--- |
| **1920 × 1080** | **PASSED** | Expansive 12-column grid, fluid typography, large trajectory timeline, full-width TextLoop. |
| **1792 × 855** | **PASSED** | 90% horizontal space utilization at 100% zoom, balanced vertical pacing, no dead voids. |
| **1440 × 900** | **PASSED** | Spacious editorial columns, side-by-side hero and developer layouts. |
| **1366 × 768** | **PASSED** | Scaled font clamps, balanced hero trajectory height. |
| **1280 × 800** | **PASSED** | Clean margins, zero horizontal overflow. |
| **1024 × 768 (Tablet)** | **PASSED** | 2-column stacked layout, 3x2 causal stages, proportional developer card. |
| **390 × 844 (Mobile)** | **PASSED** | Single-column vertical flow, full-width touch targets, responsive TextLoop wave. |

---

## 7. Automated Tests & Production Build

- **Unit Tests**:
  - `TextLoopComponent` (4 tests passed).
  - `DeveloperProfileCardComponent` (6 tests passed).
  - `LandingPageComponent` (8 tests passed).
  - All investigation and core specs (63 tests passed).
  - **Total**: **21 test files, 81/81 unit tests passed** (`npm test -- --watch=false`).
- **Production Build**: `ng build` succeeded with **0 errors** (604 kB main bundle).

---

## 8. Files Changed

| File | Type | Description |
| :--- | :--- | :--- |
| `apps/frontend/src/app/shared/components/text-loop/text-loop.component.ts` | Component | Native Angular TextLoop component with GSAP continuous textPath animation. |
| `apps/frontend/src/app/shared/components/text-loop/text-loop.component.html` | Template | SVG textPath template with background ribbon and measurement node. |
| `apps/frontend/src/app/shared/components/text-loop/text-loop.component.css` | Styles | TextLoop styles with reduced-motion overrides. |
| `apps/frontend/src/app/shared/components/text-loop/text-loop.component.spec.ts` | Tests | Unit test suite for TextLoopComponent. |
| `apps/frontend/src/app/pages/landing/landing.component.html` | Template | Redesigned full-width story-driven landing page with Hero, TextLoop, Mission, How It Works, Investigation, Developer, and Access sections. |
| `apps/frontend/src/app/pages/landing/landing.component.ts` | Logic | Updated signals, navigation anchors, investigation steps, and trajectory stages. |
| `apps/frontend/src/app/pages/landing/landing.component.css` | Styles | Updated with fluid typography and laser scan transition curtain. |
| `apps/frontend/src/app/pages/landing/landing.component.spec.ts` | Tests | Updated tests verifying all 6 sections and TextLoop banner. |
| `docs/phases/PHASE_21_LANDING_PAGE_REWORK.md` | Docs | Phase 21 Landing Page 2.0 release documentation. |

---

## 9. Remaining Issues
None. The full-width, story-driven landing page is completely functional, responsive, tested, and running locally on `http://localhost:4200/`.
