import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { AnalysisSession } from '../../core/models';

@Component({
  selector: 'app-analyses',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="space-y-8 animate-reveal">
      <!-- Top Title Bar -->
      <div class="flex flex-wrap items-center justify-between gap-4 border-b border-(--grid) pb-6">
        <div>
          <div class="text-[10px] font-mono tracking-widest text-(--or) uppercase mb-1">
            03 / INVESTIGATION CONTROL SURFACE
          </div>
          <h1 class="text-3xl font-extrabold tracking-tight text-(--ink) flex items-center gap-3 uppercase">
            Autonomous Analysis Runs & Sessions
          </h1>
          <p class="text-xs font-mono text-(--muted) mt-1">
            Real-time workflow execution states across LangGraph exploration and synthesis pipelines.
          </p>
        </div>
      </div>

      <!-- Analysis Sessions List -->
      <div class="space-y-4 font-mono">
        @for (analysis of analyses(); track analysis.id) {
          <div class="bento-card p-6 space-y-4 group">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div class="flex items-center gap-3">
                <span class="px-2 py-0.5 rounded text-[10px] font-bold bento-card-elevated text-(--or)">
                  RUN #{{ analysis.id.slice(0, 8) }}
                </span>
                <span class="text-sm font-bold text-(--ink)">
                  {{ analysis.version_a.name }} <span class="text-(--or)">→</span> {{ analysis.version_b.name }}
                </span>
              </div>
              <span class="px-2.5 py-1 text-xs font-bold rounded uppercase bg-emerald-950/80 text-emerald-400 border border-emerald-800">
                {{ analysis.status }}
              </span>
            </div>

            <!-- Pipeline Execution Progress Timeline -->
            <div class="p-4 bento-card-elevated space-y-2">
              <div class="flex items-center justify-between text-xs text-(--muted)">
                <span>STAGE: <strong class="text-(--ink)">SYNTHESIS & REPORTING</strong></span>
                <span>PROGRESS: <strong class="text-emerald-400">100%</strong></span>
              </div>
              <div class="w-full bg-(--surface) h-2 rounded-full overflow-hidden border border-(--grid)">
                <div class="bg-(--or) h-full w-full"></div>
              </div>
            </div>

            <!-- Stats & Meta -->
            <div class="flex flex-wrap items-center justify-between gap-4 pt-2 text-xs text-(--muted)">
              <div class="flex items-center gap-4">
                <span>EXPLORED: <strong class="text-(--ink)">{{ analysis.workflows_explored }} Workflows</strong></span>
                <span>•</span>
                <span>DETECTED: <strong class="text-rose-400">{{ analysis.regressions_count }} Regressions</strong></span>
              </div>

              <a
                routerLink="/investigations"
                class="inline-flex items-center gap-1.5 text-xs text-(--or) font-bold hover:underline"
              >
                Inspect Generated Test Packages →
              </a>
            </div>
          </div>
        } @empty {
          <div class="p-12 text-center bento-card text-xs text-(--muted)">
            No analysis sessions found.
          </div>
        }
      </div>
    </div>
  `,
})
export class AnalysesComponent implements OnInit {
  private readonly api = inject(ApiService);
  readonly analyses = signal<AnalysisSession[]>([]);

  ngOnInit(): void {
    this.api.getAnalyses().subscribe((data) => this.analyses.set(data));
  }
}
