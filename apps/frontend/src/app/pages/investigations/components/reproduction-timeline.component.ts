import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReproductionResult, ReproductionStep } from '../../../core/models/investigation.models';
import { StatusBadgeComponent } from './status-badge.component';

@Component({
  selector: 'app-reproduction-timeline',
  standalone: true,
  imports: [CommonModule, StatusBadgeComponent],
  template: `
    <div class="space-y-6 font-mono">
      <!-- Reproduction Header Card -->
      <div class="bento-card p-5 border border-(--grid) flex flex-wrap items-center justify-between gap-4">
        <div class="space-y-1">
          <div class="flex items-center gap-3">
            <h3 class="text-sm font-bold text-(--ink) uppercase">Deterministic Replay Execution</h3>
            <app-status-badge [status]="reproduction?.status || 'NOT_ATTEMPTED'"></app-status-badge>
          </div>
          <p class="text-xs text-(--muted)">
            Reconstructed minimal causal path verifying regression in fresh browser context.
          </p>
        </div>

        <div class="flex items-center gap-4 text-xs">
          <div class="p-2.5 rounded bento-card-elevated border border-(--grid) text-center">
            <span class="block text-(--muted) text-[10px]">STRATEGY</span>
            <span class="font-bold text-(--ink)">{{ reproduction?.strategy || 'DIRECT_REPLAY' }}</span>
          </div>
          <div class="p-2.5 rounded bento-card-elevated border border-(--grid) text-center">
            <span class="block text-(--muted) text-[10px]">TOTAL DURATION</span>
            <span class="font-bold text-(--or)">{{ formatDuration(reproduction?.total_duration_ms) }}</span>
          </div>
          <div class="p-2.5 rounded bento-card-elevated border border-(--grid) text-center">
            <span class="block text-(--muted) text-[10px]">ATTEMPTS</span>
            <span class="font-bold text-(--ink)">{{ reproduction?.attempts?.length || 0 }}</span>
          </div>
        </div>
      </div>

      <!-- Verification Notes if available -->
      <div
        *ngIf="reproduction?.final_verification"
        class="p-4 rounded bento-card-elevated border border-(--grid) text-xs flex items-start gap-3"
      >
        <span class="text-base">🔍</span>
        <div>
          <span class="font-bold text-(--ink) block">Verification Match: {{ reproduction?.final_verification?.match_status }}</span>
          <span class="text-(--muted)">{{ reproduction?.final_verification?.notes || 'Empirical evidence matches expected regression profile.' }}</span>
        </div>
      </div>

      <!-- Causal Replay Step Timeline -->
      <div class="space-y-3">
        <h4 class="text-xs font-bold text-(--ink) uppercase tracking-wider">
          Causal Replay Sequence ({{ reproduction?.path?.steps?.length || 0 }} Steps)
        </h4>

        <div *ngIf="!reproduction?.path?.steps?.length" class="p-6 rounded bento-card-elevated border border-(--grid) text-center text-(--muted) text-xs">
          No causal reproduction action steps available.
        </div>

        <div class="space-y-2.5">
          <div
            *ngFor="let step of reproduction?.path?.steps || []; let idx = index"
            class="p-3.5 rounded bento-card border border-(--grid) hover:border-(--or) flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition"
          >
            <!-- Step index and Action Type -->
            <div class="flex items-center gap-3">
              <span class="h-6 w-6 rounded-full bg-(--surface) border border-(--grid) flex items-center justify-center text-xs font-bold text-(--or)">
                {{ idx + 1 }}
              </span>
              <span
                class="px-2 py-0.5 rounded text-xs uppercase font-bold"
                [ngClass]="getActionClass(step.action_type)"
              >
                {{ step.action_type }}
              </span>
            </div>

            <!-- Target / Target strategy -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-xs font-bold text-(--ink) truncate">
                  {{ step.accessible_name || step.stable_target_identity || step.raw_target || 'Target Window' }}
                </span>
                <span *ngIf="step.target_role" class="px-1.5 py-0.5 rounded bento-card-elevated text-[9px] text-(--muted) border border-(--grid)">
                  role: {{ step.target_role }}
                </span>
              </div>
              <div class="text-[10px] text-(--muted) truncate mt-0.5">
                Strategy: {{ step.target_strategy }} &bull; Locator: {{ step.stable_target_identity || step.raw_target || '-' }}
              </div>
            </div>

            <!-- Value / Input -->
            <div *ngIf="step.value" class="px-2.5 py-1 rounded bento-card-elevated text-xs text-(--or) border border-(--grid)">
              Value: "{{ step.value }}"
            </div>

            <!-- Timeout -->
            <div class="text-[10px] text-(--muted)">
              {{ step.timeout_ms }}ms
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class ReproductionTimelineComponent {
  @Input() reproduction: ReproductionResult | null = null;

  formatDuration(ms?: number): string {
    if (!ms) return '0.00 ms';
    return `${ms.toFixed(2)} ms`;
  }

  getActionClass(actionType: string): string {
    const act = actionType.toUpperCase();
    if (act.includes('NAVIGAT')) return 'bg-blue-500/10 text-blue-500 border border-blue-500/30';
    if (act.includes('CLICK')) return 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/30';
    if (act.includes('TYPE')) return 'bg-amber-500/10 text-amber-500 border border-amber-500/30';
    if (act.includes('WAIT')) return 'bg-purple-500/10 text-purple-500 border border-purple-500/30';
    return 'bg-stone-500/10 text-stone-400 border border-stone-500/30';
  }
}
