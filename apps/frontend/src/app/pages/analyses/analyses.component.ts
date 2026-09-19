import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';
import { AnalysisSession } from '../../core/models';

@Component({
  selector: 'app-analyses',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="space-y-6">
      <div class="flex items-center justify-between border-b border-slate-800 pb-5">
        <div>
          <h1 class="text-2xl font-bold tracking-tight text-white">Analysis Sessions</h1>
          <p class="text-sm text-slate-400 mt-1">Autonomous Version A/B comparative exploration and regression runs</p>
        </div>
      </div>

      <div class="space-y-3">
        @for (analysis of analyses(); track analysis.id) {
          <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
            <div>
              <div class="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <span>{{ analysis.version_a.name }}</span>
                <span class="text-slate-500">vs</span>
                <span>{{ analysis.version_b.name }}</span>
              </div>
              <div class="text-xs text-slate-400 mt-1">
                Explored: {{ analysis.workflows_explored }} workflows • Regressions: {{ analysis.regressions_count }}
              </div>
            </div>
            <span class="px-2.5 py-1 text-xs font-semibold rounded-full bg-slate-800 text-slate-300 border border-slate-700 uppercase">
              {{ analysis.status }}
            </span>
          </div>
        } @empty {
          <div class="p-8 text-center rounded-xl bg-slate-900 border border-slate-800 text-slate-400 text-sm">
            No active or past analysis runs found.
          </div>
        }
      </div>
    </div>
  `
})
export class AnalysesComponent implements OnInit {
  private readonly api = inject(ApiService);
  readonly analyses = signal<AnalysisSession[]>([]);

  ngOnInit(): void {
    this.api.getAnalyses().subscribe((data) => this.analyses.set(data));
  }
}
