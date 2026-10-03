# RETRACE — PHASE 21: LANDING PAGE SPATIAL COMPOSITION FINAL
**Spacious • Editorial • Cinematic • Minimal • Scroll-Driven**

---

## 1. Previous Density Problems Diagnosed

The earlier iterations suffered from **excessive vertical compression**:
- Multiple core sections (Mission, Causal Path, How It Works, 4 capability cards, Developer) were appearing inside a single or cramped viewport.
- This created a "dashboard" look rather than a spacious, long-form editorial product journey.
- The solution was not to make cards smaller, but to **give each major concept its own visual moment (~75vh to 100vh)** and encourage intentional scrolling.

---

## 2. New Section Architecture & Viewport Strategy

The page is structured into **5 distinct chapters**, each occupying its own visual moment:

```
01 // HERO (~85–100vh)
     "What is RETRACE?"
     - TechText canvas wordmark
     - Primary headline: "Find what changed. Prove why it changed."
     - Supporting text
     - Primary CTA [ ENTER RETRACE → ]
     - Minimal causal topology visual (Version A → Observe → Difference → Evidence → Root Cause → Version B)
     ↓
02 // MISSION & CAUSAL PATH (~75–90vh)
     "Why does RETRACE exist?"
     - Statement: "Eliminating guesswork from regression diagnosis."
     - Concise supporting text
     - Compact 6-stage continuous horizontal causal flow with generous breathing room around it
     ↓
03 // HOW IT WORKS (~80–100vh)
     "How does RETRACE investigate?"
     - Heading: "From behavior to explanation."
     - 4-stage flowing process (01 Observe → 02 Compare → 03 Explain → 04 Reproduce)
     - Intrinsic height blocks (no giant empty card interiors)
     ↓
04 // THE DEVELOPER (~75–90vh)
     "Who built it?"
     - Real portrait image: `snf.jpg` (35–40% width on desktop, rounded-[24px])
     - Name: Guruprasad Bhosale (BUILDER OF RETRACE)
     - Authentic bio
     - Verified clean text links (GITHUB ↗, LINKEDIN ↗)
     ↓
05 // ACCESS RETRACE & FOOTER (~60–75vh)
     "Enter the product"
     - Large headline: "READY TO INVESTIGATE?"
     - Supporting text: "Trace the regression. Follow the evidence."
     - Grand entry CTA: [ ENTER RETRACE → ]
     - Minimal single-row footer (RETRACE • Guruprasad Bhosale • GitHub ↗ • LinkedIn ↗ • © 2026)
```

---

## 3. Spacing & Rhythm System

- **Viewport Presence**: Every section has an intentional `min-h-[75vh]` to `min-h-[90vh]` on desktop with `py-20 lg:py-32` padding.
- **Whitespace Allocation**: Generous whitespace is placed **around** graphics and between chapters—never wasted inside bloated empty cards.
- **Separators**: Clean ruled horizontal dividers with subtle orange (`var(--or)`) registration marks anchor section boundaries.

---

## 4. Typography Hierarchy

| Level | Component | Specs |
| :--- | :--- | :--- |
| **Level 1** | Hero Headline | Space Grotesk / Inter Tight (48px–72px, font-extrabold, line-height: 1.08) |
| **Level 2** | Section Headings | Space Grotesk (32px–48px, font-extrabold, tracking-tight) |
| **Level 3** | Developer Name | Space Grotesk (32px–48px, font-extrabold) |
| **Level 4** | Body & Descriptions | Inter / system-ui (14px–18px, leading-relaxed, text-[var(--muted)]) |
| **Level 5** | Numerals & Metadata | JetBrains Mono (10px–12px, font-bold, uppercase, tracking-widest) |

---

## 5. Developer Section (`snf.jpg`)

- **Asset Path**: `G:\RETRACE\snf.jpg` copied into `apps/frontend/public/snf.jpg` and served directly as `/snf.jpg`.
- **Styling**: `rounded-[24px]`, border `var(--grid)`, 35–40% width in editorial 12-column grid.
- **Copy**:
  - Name: **Guruprasad Bhosale**
  - Subtitle: `BUILDER OF RETRACE.`
  - Bio: *"Final-year B.Tech student building RETRACE as an exploration of autonomous software debugging, evidence-driven investigation, and intelligent engineering systems."*
  - Links: [GitHub ↗](https://github.com/Guruprasad-Bhosale) and [LinkedIn ↗](https://www.linkedin.com/in/guruprasad-bhosale)

---

## 6. Motion & Interaction

- **Hero & Wordmark**: Interactive `TechText` SVG canvas with smooth sweep and particle specks.
- **Command Center Transition**: Smooth cinematic laser scan curtain overlay (`transition-curtain`) upon clicking `ENTER RETRACE →`.
- **Reduced Motion**: Full `prefers-reduced-motion: reduce` CSS override for instant zero-animation execution.

---

## 7. Responsive Behavior

- **Desktop (1440px / 1280px)**: 12-column asymmetric layout with dedicated full-screen moments per section.
- **Tablet (1024px / 768px)**: 2-column responsive layout, 3x2 causal stages, proportional portrait image.
- **Mobile (390px / 375px)**: Single column vertical flow, 2-column causal path, full-width CTA touch targets, zero horizontal overflow.

---

## 8. Automated Tests & Build

- **Unit Tests**: `apps/frontend/src/app/pages/landing/landing.component.spec.ts`
  - 19 test files passed, 70/70 unit tests passed (`npm test -- --watch=false`).
- **Production Build**: `ng build` succeeded with 0 errors (512 kB JS, 85 kB CSS).

---

## 9. Files Changed

| File | Type | Description |
| :--- | :--- | :--- |
| `apps/frontend/public/snf.jpg` | Asset | Real profile image copied from `G:\RETRACE\snf.jpg`. |
| `apps/frontend/src/app/pages/landing/landing.component.html` | Template | Long-form scroll-driven editorial layout (Hero, Mission, How It Works, Developer, CTA). |
| `apps/frontend/src/app/pages/landing/landing.component.ts` | Logic | Cleaned up signals, navigation handlers, transition curtain, and fallback error handling. |
| `apps/frontend/src/app/pages/landing/landing.component.css` | Styles | Editorial typography, transition laser curtain, reduced motion support. |
| `apps/frontend/src/app/pages/landing/landing.component.spec.ts` | Tests | Verified unit tests for 5-section structure, CTA routing, developer links, and zero placeholders. |
| `docs/phases/PHASE_21_LANDING_PAGE_SPACIAL_COMPOSITION.md` | Docs | Phase 21 spatial composition documentation. |

---

## 10. Remaining Issues
None. The landing page is completely functional, spacious, minimal, tested, and running locally on `http://localhost:4200/`.
