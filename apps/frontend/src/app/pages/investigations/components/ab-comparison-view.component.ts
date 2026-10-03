import { Component, Input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  ClassificationEvidence,
  RegressionClassification,
  ReproductionResult,
} from '../../../core/models/investigation.models';

@Component({
  selector: 'app-ab-comparison-view',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="space-y-6 font-mono">
      <!-- Section Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-(--grid) pb-3">
        <div>
          <div class="flex items-center gap-2">
            <span class="text-sm text-(--or)">⚖️</span>
            <h3 class="text-sm font-bold text-(--ink) uppercase tracking-wider">
              Dual-Version A/B Differential Visualizer
            </h3>
          </div>
          <p class="text-xs text-(--muted) mt-0.5">
            Synchronized comparison between baseline state (Version A) and candidate regression state (Version B).
          </p>
        </div>

        <!-- Slider Split Controls -->
        <div class="flex items-center gap-3 bg-(--surface) border border-(--grid) px-3 py-1.5 rounded">
          <span class="text-[10px] text-(--muted) uppercase font-bold">Split Splitter:</span>
          <input
            type="range"
            min="10"
            max="90"
            [(ngModel)]="splitPercentage"
            class="w-28 accent-(--or) cursor-pointer"
            aria-label="A/B visual diff split slider"
          />
          <span class="text-[10px] font-bold text-(--or) min-w-[32px]">{{ splitPercentage }}%</span>
        </div>
      </div>

      <!-- Comparative Side-by-Side Dual Deck -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Version A: Baseline -->
        <div class="bento-card p-5 border border-emerald-900/60 space-y-4">
          <div class="flex items-center justify-between border-b border-(--grid) pb-3">
            <div class="flex items-center gap-2.5">
              <span class="h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
              <h4 class="text-xs font-bold text-(--ink) uppercase">Version A (Baseline)</h4>
            </div>
            <span class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 text-[10px] font-bold border border-emerald-800">
              EXPECTED
            </span>
          </div>

          <!-- Observed Parameters -->
          <div class="space-y-3 text-xs">
            <div>
              <span class="text-(--muted) block text-[10px] uppercase font-bold">Observed Value / State:</span>
              <div class="p-2.5 rounded bento-card-elevated text-emerald-500 border border-(--grid) mt-1 font-bold">
                {{ getExpectedValue() }}
              </div>
            </div>

            <div *ngIf="getExpectedUrl()">
              <span class="text-(--muted) block text-[10px] uppercase font-bold">Destination Route:</span>
              <div class="p-2.5 rounded bento-card-elevated text-(--ink) border border-(--grid) mt-1 truncate">
                {{ getExpectedUrl() }}
              </div>
            </div>

            <div *ngIf="getExpectedStatus()">
              <span class="text-(--muted) block text-[10px] uppercase font-bold">HTTP Status:</span>
              <div class="p-2.5 rounded bento-card-elevated text-(--ink) border border-(--grid) mt-1 font-bold">
                {{ getExpectedStatus() }} OK
              </div>
            </div>
          </div>
        </div>

        <!-- Version B: Candidate / Regressed -->
        <div class="bento-card p-5 border border-rose-900/60 space-y-4">
          <div class="flex items-center justify-between border-b border-(--grid) pb-3">
            <div class="flex items-center gap-2.5">
              <span class="h-2.5 w-2.5 rounded-full bg-rose-500 animate-pulse"></span>
              <h4 class="text-xs font-bold text-(--ink) uppercase">Version B (Candidate)</h4>
            </div>
            <span class="px-2 py-0.5 rounded bg-rose-950 text-rose-400 text-[10px] font-bold border border-rose-800">
              REGRESSION
            </span>
          </div>

          <!-- Observed Parameters -->
          <div class="space-y-3 text-xs">
            <div>
              <span class="text-(--muted) block text-[10px] uppercase font-bold">Observed Value / State:</span>
              <div class="p-2.5 rounded bento-card-elevated text-rose-500 border border-(--grid) mt-1 font-bold">
                {{ getActualValue() }}
              </div>
            </div>

            <div *ngIf="getActualUrl()">
              <span class="text-(--muted) block text-[10px] uppercase font-bold">Destination Route:</span>
              <div class="p-2.5 rounded bento-card-elevated text-(--ink) border border-(--grid) mt-1 truncate">
                {{ getActualUrl() }}
              </div>
            </div>

            <div *ngIf="getActualStatus()">
              <span class="text-(--muted) block text-[10px] uppercase font-bold">HTTP Status:</span>
              <div class="p-2.5 rounded bento-card-elevated text-rose-500 border border-(--grid) mt-1 font-bold">
                {{ getActualStatus() }} ERROR / MISMATCH
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Granular Difference Annotations Table -->
      <div class="bento-card p-5 border border-(--grid) space-y-3">
        <div class="flex items-center justify-between">
          <h4 class="text-xs font-bold text-(--ink) uppercase tracking-wider">
            Difference Payload Annotations
          </h4>
          <span class="text-[10px] text-(--muted)">
            {{ getDetailEntries().length }} ANNOTATED FIELDS
          </span>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-xs text-left">
            <thead>
              <tr class="border-b border-(--grid) text-(--muted) text-[10px]">
                <th class="py-2 px-3">PROPERTY</th>
                <th class="py-2 px-3">EVIDENCE DETAIL</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-(--grid)">
              <tr
                *ngFor="let entry of getDetailEntries()"
                class="hover:bg-(--surface) transition"
              >
                <td class="py-2 px-3 font-bold text-(--ink)">{{ entry.key }}</td>
                <td class="py-2 px-3 text-(--muted) font-mono">{{ entry.val }}</td>
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

  splitPercentage = 50;

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
