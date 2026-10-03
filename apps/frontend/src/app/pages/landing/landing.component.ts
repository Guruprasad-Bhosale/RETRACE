import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { ThemeService } from '../../core/services/theme.service';
import { TechTextComponent } from '../../shared/components/tech-text/tech-text.component';
import { DeveloperProfileCardComponent } from '../../shared/components/developer-profile-card/developer-profile-card.component';
import { TextLoopComponent } from '../../shared/components/text-loop/text-loop.component';
import { StrokeTextComponent } from '../../shared/components/stroke-text/stroke-text.component';

export interface CausalStage {
  num: string;
  title: string;
  status: string;
  detail?: string;
}

export interface WorkflowStage {
  num: string;
  title: string;
  summary: string;
}

export interface InvestigationStep {
  num: string;
  title: string;
  descriptor: string;
  explanation: string;
}

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    TechTextComponent,
    DeveloperProfileCardComponent,
    TextLoopComponent,
    StrokeTextComponent,
  ],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.css',
})
export class LandingPageComponent implements OnInit {
  readonly themeService = inject(ThemeService);
  private readonly router = inject(Router);

  // Transition & Interactive State Signals
  readonly isTransitioning = signal<boolean>(false);
  readonly mobileNavOpen = signal<boolean>(false);
  readonly hoveredTrajectoryIndex = signal<number | null>(null);
  readonly activeInvestigationIndex = signal<number>(2); // Default to DIFFERENCE

  // Story-Driven Navigation Anchors
  readonly landingNavItems = [
    { label: 'THE PROBLEM', anchor: '#mission' },
    { label: 'THE METHOD', anchor: '#how-it-works' },
    { label: 'THE INVESTIGATION', anchor: '#investigation' },
    { label: 'THE MIND BEHIND IT', anchor: '#developer' },
  ];

  // 01 // Hero Forensic Trajectory Stages (Clean Vertical Timeline)
  readonly heroTrajectoryStages: CausalStage[] = [
    { num: '01', title: 'VERSION A', status: 'BASELINE' },
    { num: '02', title: 'OBSERVE', status: 'RUNTIME CAPTURE' },
    { num: '03', title: 'DIFFERENCE', status: 'BEHAVIORAL DELTA' },
    { num: '04', title: 'EVIDENCE', status: 'CAUSAL GRAPH' },
    { num: '05', title: 'ROOT CAUSE', status: 'AST DIFF' },
    { num: '06', title: 'VERSION B', status: 'EXPLAINED' },
  ];

  // 02 // MISSION: 6 Compact Causal Stages
  readonly causalStages: CausalStage[] = [
    { num: '01', title: 'VERSION A', status: 'BASELINE' },
    { num: '02', title: 'BEHAVIOR', status: 'OBSERVED' },
    { num: '03', title: 'DIFFERENCE', status: 'DETECTED' },
    { num: '04', title: 'EVIDENCE', status: 'VERIFIED' },
    { num: '05', title: 'ROOT CAUSE', status: 'LOCATED' },
    { num: '06', title: 'VERSION B', status: 'EXPLAINED' },
  ];

  // 03 // HOW IT WORKS: 4 Flowing Process Steps
  readonly workflowStages: WorkflowStage[] = [
    {
      num: '01',
      title: 'OBSERVE',
      summary: 'Capture what actually happened across DOM, network, and execution logs.',
    },
    {
      num: '02',
      title: 'COMPARE',
      summary: 'Find where execution trajectories and state transitions diverged.',
    },
    {
      num: '03',
      title: 'EXPLAIN',
      summary: 'Trace behavioral anomalies directly to source commits and AST diffs.',
    },
    {
      num: '04',
      title: 'REPRODUCE',
      summary: 'Synthesize deterministic reproduction tests and verify failure offline.',
    },
  ];

  // 04 // THE INVESTIGATION: Forensic Trail Breakdown
  readonly investigationSteps: InvestigationStep[] = [
    {
      num: '01',
      title: 'OBSERVE',
      descriptor: 'Runtime behavior captured.',
      explanation:
        'Captures multi-modal telemetry—DOM mutations, console events, and network HAR streams—under isolated, reproducible browser environments.',
    },
    {
      num: '02',
      title: 'DIFFERENCE',
      descriptor: 'Behavioral divergence isolated.',
      explanation:
        'Aligns baseline Version A and candidate Version B execution timelines to detect semantic state and UI divergence without probabilistic guessing.',
    },
    {
      num: '03',
      title: 'EVIDENCE',
      descriptor: 'Observations become causal evidence.',
      explanation:
        'Constructs an immutable causal DAG linking user interactions, state transitions, and network responses to prove causality.',
    },
    {
      num: '04',
      title: 'ROOT CAUSE',
      descriptor: 'Source change localized.',
      explanation:
        'Traverses the evidence graph down to specific git commits, AST nodes, and symbol modifications that introduced the behavioral shift.',
    },
    {
      num: '05',
      title: 'REPRODUCE',
      descriptor: 'The regression is independently verified.',
      explanation:
        'Synthesizes standalone Playwright TypeScript reproduction tests that deterministically reproduce and verify the failure path.',
    },
  ];

  ngOnInit(): void {
    if (typeof window !== 'undefined' && window.location.hash) {
      setTimeout(() => {
        const el = document.querySelector(window.location.hash);
        if (el) el.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  }

  toggleMobileNav(): void {
    this.mobileNavOpen.update((v) => !v);
  }

  closeMobileNav(): void {
    this.mobileNavOpen.set(false);
  }

  setHoveredTrajectory(index: number | null): void {
    this.hoveredTrajectoryIndex.set(index);
  }

  selectInvestigationStep(index: number): void {
    this.activeInvestigationIndex.set(index);
  }

  /**
   * Controlled transition from Public Landing Page to RETRACE Command Center.
   * Respects prefers-reduced-motion.
   */
  enterRetrace(): void {
    if (
      typeof window !== 'undefined' &&
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ) {
      this.router.navigate(['/dashboard']).then(() => {
        if (typeof window !== 'undefined') {
          window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
        }
      });
      return;
    }

    this.isTransitioning.set(true);
    setTimeout(() => {
      this.router.navigate(['/dashboard']).then(() => {
        this.isTransitioning.set(false);
        if (typeof window !== 'undefined') {
          window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
        }
      });
    }, 550);
  }

  scrollToSection(anchor: string, e?: Event): void {
    if (e) {
      e.preventDefault();
    }
    this.closeMobileNav();
    if (typeof document === 'undefined' || typeof window === 'undefined') return;

    const target = document.querySelector(anchor) as HTMLElement | null;
    if (!target) return;

    // Calculate header height & consistent breathing room offset
    const headerEl = document.querySelector('header');
    const headerHeight = headerEl ? headerEl.getBoundingClientRect().height : 72;
    const targetRect = target.getBoundingClientRect();
    const scrollTarget = window.scrollY + targetRect.top - (headerHeight + 24);

    window.scrollTo({
      top: Math.max(0, scrollTarget),
      behavior: 'smooth',
    });

    if (typeof history !== 'undefined' && history.pushState) {
      history.pushState(null, '', anchor);
    }
  }
}
