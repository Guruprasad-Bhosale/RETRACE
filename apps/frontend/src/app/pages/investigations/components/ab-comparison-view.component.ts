import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ClassificationEvidence,
  RegressionClassification,
  ReproductionResult,
} from '../../../core/models/investigation.models';

@Component({
  selector: 'app-ab-comparison-view',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-base font-semibold text-slate-100 flex items-center gap-2">
            <span class="text-indigo-400 font-mono">⚖️</span>
            Dual-Version A/B Comparative Analysis
          </h3>
          <p class="text-xs text-slate-400 mt-0.5">
            Direct comparison between baseline expected state (Version A) and observed regressed state (Version B).
          </p>
        </div>
      </div>

      <!-- Comparative Side-by-Side Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Version A: Baseline -->
        <div class="p-5 rounded-xl bg-slate-900 border border-emerald-900/60 shadow-sm space-y-4">
          <div class="flex items-center justify-between border-b border-slate-800 pb-3">
            <div class="flex items-center gap-2.5">
              <span class="h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
              <h4 class="text-sm font-bold text-slate-100">Version A (Baseline)</h4>
            </div>
            <span class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 text-xs font-mono font-semibold border border-emerald-800">
              EXPECTED
            </span>
          </div>

          <!-- Observed Parameters -->
          <div class="space-y-3 text-xs">
            <div>
              <span class="text-slate-500 block font-medium">Observed Value / State:</span>
              <div class="p-2.5 rounded bg-slate-950 font-mono text-emerald-300 border border-slate-800 mt-1">
                {{ getExpectedValue() }}
              </div>
            </div>

            <div *ngIf="getExpectedUrl()">
              <span class="text-slate-500 block font-medium">Destination Route:</span>
              <div class="p-2.5 rounded bg-slate-950 font-mono text-slate-200 border border-slate-800 mt-1 truncate">
                {{ getExpectedUrl() }}
              </div>
            </div>

            <div *ngIf="getExpectedStatus()">
              <span class="text-slate-500 block font-medium">HTTP Status Code:</span>
              <div class="p-2.5 rounded bg-slate-950 font-mono text-slate-200 border border-slate-800 mt-1">
                {{ getExpectedStatus() }}
              </div>
            </div>
          </div>
        </div>

        <!-- Version B: Candidate / Regressed -->
        <div class="p-5 rounded-xl bg-slate-900 border border-rose-900/60 shadow-sm space-y-4">
          <div class="flex items-center justify-between border-b border-slate-800 pb-3">
            <div class="flex items-center gap-2.5">
              <span class="h-2.5 w-2.5 rounded-full bg-rose-500"></span>
              <h4 class="text-sm font-bold text-slate-100">Version B (Candidate)</h4>
            </div>
            <span class="px-2 py-0.5 rounded bg-rose-950 text-rose-400 text-xs font-mono font-semibold border border-rose-800">
              REGRESSION
            </span>
          </div>

          <!-- Observed Parameters -->
          <div class="space-y-3 text-xs">
            <div>
              <span class="text-slate-500 block font-medium">Observed Value / State:</span>
              <div class="p-2.5 rounded bg-slate-950 font-mono text-rose-300 border border-slate-800 mt-1">
                {{ getActualValue() }}
              </div>
            </div>

            <div *ngIf="getActualUrl()">
              <span class="text-slate-500 block font-medium">Destination Route:</span>
              <div class="p-2.5 rounded bg-slate-950 font-mono text-slate-200 border border-slate-800 mt-1 truncate">
                {{ getActualUrl() }}
              </div>
            </div>

            <div *ngIf="getActualStatus()">
              <span class="text-slate-500 block font-medium">HTTP Status Code:</span>
              <div class="p-2.5 rounded bg-slate-950 font-mono text-rose-300 border border-slate-800 mt-1">
                {{ getActualStatus() }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Granular Difference Details Table -->
      <div class="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
        <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider">
          Granular Evidence Difference Payload
        </h4>
        <div class="overflow-x-auto">
          <table class="w-full text-xs text-left">
            <thead>
              <tr class="border-b border-slate-800 text-slate-400 font-mono">
                <th class="py-2 px-3">PROPERTY</th>
                <th class="py-2 px-3">EVIDENCE DETAIL</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/60 font-mono">
              <tr *ngFor="let entry of getDetailEntries()">
                <td class="py-2.5 px-3 font-semibold text-slate-300">{{ entry.key }}</td>
                <td class="py-2.5 px-3 text-slate-400">{{ entry.val }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
})
export class AbComparisonViewComponent {
  @Input() classification: RegressionClassification | null = null;
  @Input() reproduction: ReproductionResult | null = null;

  getExpectedValue(): string {
    const d = this.classification?.evidence?.details;
    if (!d) return 'Baseline standard behavior';
    return String(d['expected_value'] || d['text_a'] || d['value_a'] || 'Expected behavior confirmed');
  }

  getActualValue(): string {
    const d = this.classification?.evidence?.details;
    if (!d) return 'Discrepancy detected';
    return String(d['actual_value'] || d['text_b'] || d['value_b'] || 'Regression anomaly observed');
  }

  getExpectedUrl(): string | null {
    const d = this.classification?.evidence?.details;
    if (!d) return null;
    return (d['expected_url'] || d['url_a']) as string | null;
  }

  getActualUrl(): string | null {
    const d = this.classification?.evidence?.details;
    if (!d) return null;
    return (d['actual_url'] || d['url_b']) as string | null;
  }

  getExpectedStatus(): number | null {
    const d = this.classification?.evidence?.details;
    if (!d) return null;
    return (d['status_a'] || d['expected_status']) as number | null;
  }

  getActualStatus(): number | null {
    const d = this.classification?.evidence?.details;
    if (!d) return null;
    return (d['status_b'] || d['actual_status']) as number | null;
  }

  getDetailEntries(): { key: string; val: string }[] {
    const d = this.classification?.evidence?.details || {};
    return Object.entries(d).map(([k, v]) => ({
      key: k,
      val: typeof v === 'object' ? JSON.stringify(v) : String(v),
    }));
  }
}
