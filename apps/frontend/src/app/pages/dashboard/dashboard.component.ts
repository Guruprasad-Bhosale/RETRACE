import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { InvestigationService } from '../../core/services/investigation.service';
import { TechTextComponent } from '../../shared/components/tech-text/tech-text.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, TechTextComponent],
  template: `
    <div class="space-y-12 animate-reveal">
      <!-- Top Technical Coordinate Stamp -->
      <div class="flex items-center justify-between text-xs font-mono text-(--muted) border-b border-(--grid) pb-3">
        <div class="flex items-center gap-3">
          <span class="text-(--or) font-bold tracking-widest uppercase">01 / OVERVIEW</span>
          <span>•</span>
          <span>X:034 Y:128 FRAME:001</span>
        </div>
        <div>RTRC / FORENSIC WORKSTATION 3.0</div>
      </div>

      <!-- Hero Section with Animated Editorial Typography & SVG Trajectory -->
      <div class="relative overflow-hidden pt-4 pb-8">
        <!-- Background Forensic Trajectory SVG -->
        <svg
          class="absolute inset-0 w-full h-full opacity-40 pointer-events-none -z-10"
          viewBox="0 0 1200 400"
          preserveAspectRatio="xMidYMid slice"
          aria-hidden="true"
        >
          <path
            id="heroTrajectory"
            d="M 50 320 C 250 320 300 180 500 190 S 750 320 920 220 1080 80 1150 60"
            fill="none"
            stroke="var(--gs)"
            stroke-width="1.5"
            stroke-dasharray="6 8"
          />
          <path
            d="M 50 320 C 250 320 300 180 500 190 S 750 320 920 220 1080 80 1150 60"
            fill="none"
            stroke="var(--or)"
            stroke-width="2"
            stroke-dasharray="1600"
            stroke-dashoffset="0"
          />
          <!-- Traveling Forensic Pulse Point -->
          <circle r="6" fill="var(--or)">
            <animateMotion dur="8s" repeatCount="indefinite">
              <mpath href="#heroTrajectory" />
            </animateMotion>
          </circle>
          <!-- Stage Coordinate Labels -->
          <g class="m" font-family="JetBrains Mono" font-size="10" fill="var(--muted)">
            <text x="50" y="345">A · BASELINE</text>
            <text x="480" y="170">01 · OBSERVE</text>
            <text x="740" y="340">03 · DIFF</text>
            <text x="920" y="200">05 · LOCALIZE</text>
            <text x="1080" y="50">B · TARGET</text>
          </g>
        </svg>

        <!-- Registration Crosshairs -->
        <span class="reg left-0 top-0"></span>
        <span class="reg right-0 top-0"></span>

        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-end">
          <div class="lg:col-span-8 space-y-4">
            <!-- TechText Interactive Vector Wordmark (React Bits Engine) -->
            <div class="w-full h-32 sm:h-40 md:h-48 relative -ml-2">
              <app-tech-text
                text="RETRACE."
                [fontWeight]="900"
                [fontSize]="160"
                color="#ea580c"
                accentColor="#ea580c"
                reveal="letter"
                [dashLength]="4"
                [dashGap]="2"
                [specks]="15"
                [draggable]="true"
                [sweep]="true"
                [speed]="1"
              ></app-tech-text>
            </div>

            <!-- Oversized Editorial Typography Reveal -->
            <h1 class="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tighter uppercase leading-[0.88] text-(--ink) reveal-active">
              <span class="sr-only">RETRACE: </span>
              <span class="ln"><span style="--d:0.2s">SEE WHAT</span></span>
              <span class="ln r"><span style="--d:0.35s">CHANGED.</span></span>
              <span class="ln r" style="margin-top: 0.08em;"><span style="--d:0.5s">UNDERSTAND</span></span>
              <span class="ln w"><span style="--d:0.65s">WHY.</span></span>
            </h1>

            <p class="text-sm md:text-base font-mono text-(--muted) max-w-2xl pt-2 leading-relaxed">
              Autonomous software regression investigation from browser observation to source-level AST evidence. Replays, isolates, and verifies causal regressions without probabilistic hallucinations.
            </p>
          </div>


          <div class="lg:col-span-4 flex flex-col items-start lg:items-end gap-3 font-mono">
            <div class="flex flex-wrap gap-2">
              <a routerLink="/investigations" class="btn-retrace">
                <span>INSPECT CASE FILES</span>
                <span>→</span>
              </a>
              <a routerLink="/analyses" class="btn-retrace btn-retrace-subtle">
                <span>EXPLORE RUNS</span>
                <span>↓</span>
              </a>
            </div>
            <div class="text-[10px] text-(--muted) tracking-wider uppercase pt-1">
              ZERO PROBABILISTIC EVIDENCE • 100% DETERMINISTIC
            </div>
          </div>
        </div>
      </div>

      <!-- Signature 7-Stage Forensic State Machine -->
      <div class="bento-card p-6 md:p-8 space-y-5">
        <div class="flex items-center justify-between text-xs font-mono">
          <span class="font-bold text-(--ink) uppercase tracking-wider flex items-center gap-2">
            <span class="inline-block w-2 h-2 rounded-full bg-(--or) animate-pulse"></span>
            Forensic Investigation Engine (Phases 3–10)
          </span>
          <span class="text-(--muted)">7 STAGES • DETERMINISTIC PROVENANCE</span>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5 text-xs font-mono">
          <div class="bento-card-elevated p-3 text-center space-y-1">
            <div class="text-[9px] text-(--muted)">PHASE 04</div>
            <div class="font-bold text-(--ink)">OBSERVE</div>
            <div class="text-[9px] text-emerald-500">Playwright v1/v2</div>
          </div>
          <div class="bento-card-elevated p-3 text-center space-y-1">
            <div class="text-[9px] text-(--muted)">PHASE 05</div>
            <div class="font-bold text-(--ink)">ALIGN</div>
            <div class="text-[9px] text-emerald-500">Trace Matching</div>
          </div>
          <div class="bento-card-elevated p-3 text-center space-y-1">
            <div class="text-[9px] text-(--muted)">PHASE 06</div>
            <div class="font-bold text-(--ink)">DIFF</div>
            <div class="text-[9px] text-emerald-500">Semantic Engine</div>
          </div>
          <div class="bento-card-elevated p-3 text-center space-y-1">
            <div class="text-[9px] text-(--muted)">PHASE 07</div>
            <div class="font-bold text-(--ink)">CLASSIFY</div>
            <div class="text-[9px] text-emerald-500">Rule Reasoner</div>
          </div>
          <div class="bento-card-elevated p-3 text-center space-y-1">
            <div class="text-[9px] text-(--muted)">PHASE 08</div>
            <div class="font-bold text-(--ink)">REPRODUCE</div>
            <div class="text-[9px] text-emerald-500">Minimal Path</div>
          </div>
          <div class="bento-card-elevated p-3 text-center space-y-1">
            <div class="text-[9px] text-(--muted)">PHASE 09</div>
            <div class="font-bold text-(--ink)">ROOT CAUSE</div>
            <div class="text-[9px] text-emerald-500">Git / AST Lines</div>
          </div>
          <div class="bento-card-elevated p-3 text-center space-y-1 border-(--or) bg-orange-500/10">
            <div class="text-[9px] text-(--or) font-bold">PHASE 10</div>
            <div class="font-bold text-(--or)">SYNTHESIZE</div>
            <div class="text-[9px] text-(--or) font-semibold">Playwright TS</div>
          </div>
        </div>
      </div>

      <!-- Asymmetric Editorial Bento Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 font-mono">
        <!-- Bento Module 1: Recent Forensic Case Files (8 Cols) -->
        <div class="lg:col-span-8 bento-card p-6 md:p-8 space-y-5">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-base font-bold text-(--ink) uppercase tracking-wider">
                Forensic Case Files (Commerce Lab)
              </h2>
              <p class="text-xs text-(--muted) mt-0.5">
                Deterministic A/B evaluations on 6 seeded defects & 3 non-regressions.
              </p>
            </div>
            <a routerLink="/investigations" class="text-xs text-(--or) hover:underline font-bold">
              View All Case Files →
            </a>
          </div>

          <div class="space-y-3 pt-2">
            @for (inv of investigations(); track inv.investigation_id) {
              <a
                [routerLink]="['/investigations', inv.investigation_id]"
                class="bento-card-elevated p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 hover:border-(--or) transition group block no-underline"
              >
                <div>
                  <div class="text-sm font-bold text-(--ink) group-hover:text-(--or) transition flex items-center gap-2">
                    <span>{{ inv.title }}</span>
                  </div>
                  <div class="text-xs text-(--muted) mt-1 flex items-center gap-3">
                    <span>CATEGORY: <strong class="text-(--ink)">{{ inv.category }}</strong></span>
                    <span>•</span>
                    <span>ATTRIBUTED: <strong class="text-(--ink)">{{ inv.commit_hash || 'Located' }}</strong></span>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <span class="px-2.5 py-1 rounded text-[10px] font-bold uppercase bg-emerald-950/40 text-emerald-400 border border-emerald-800">
                    {{ inv.status }}
                  </span>
                </div>
              </a>
            } @empty {
              <div class="bento-card-elevated p-8 text-center text-xs text-(--muted)">
                NO INVESTIGATION RECORDED
                <div class="mt-2">
                  <a routerLink="/investigations" class="text-(--or) underline font-bold">START INVESTIGATION →</a>
                </div>
              </div>
            }
          </div>
        </div>

        <!-- Bento Module 2: System Telemetry & Invariants (4 Cols) -->
        <div class="lg:col-span-4 space-y-6">
          <div class="bento-card p-6 space-y-4">
            <div class="text-xs font-bold text-(--ink) uppercase tracking-wider">
              Operational Telemetry (Phase 15)
            </div>
            <div class="space-y-2.5 text-xs">
              <div class="flex justify-between p-2.5 bento-card-elevated">
                <span class="text-(--muted)">API LATENCY (p95):</span>
                <span class="text-emerald-500 font-bold">&lt; 18ms</span>
              </div>
              <div class="flex justify-between p-2.5 bento-card-elevated">
                <span class="text-(--muted)">REDIS QUEUE DEPTH:</span>
                <span class="text-(--ink) font-bold">0 Pending</span>
              </div>
              <div class="flex justify-between p-2.5 bento-card-elevated">
                <span class="text-(--muted)">WORKER STREAM LEASE:</span>
                <span class="text-(--ink) font-bold">XAUTOCLAIM Ready</span>
              </div>
              <div class="flex justify-between p-2.5 bento-card-elevated">
                <span class="text-(--muted)">CRASH RECOVERY:</span>
                <span class="text-emerald-500 font-bold">Guaranteed (XACK)</span>
              </div>
            </div>
          </div>

          <div class="bento-card p-6 space-y-2 text-xs">
            <div class="font-bold text-(--ink) uppercase tracking-wider text-xs">
              Evidence Integrity Rules
            </div>
            <p class="text-(--muted) leading-relaxed text-[11px]">
              RETRACE enforces strict separation between operational telemetry and empirical investigation evidence. Zero hallucinated or probabilistic claims are permitted in reports.
            </p>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class DashboardComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly invService = inject(InvestigationService);

  readonly status = this.api.systemStatus;
  readonly investigations = this.invService.investigations;
  readonly currentTime = new Date();

  ngOnInit(): void {
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    }
    this.api.getSystemStatus().subscribe();
    this.invService.loadInvestigations().subscribe();
  }
}
