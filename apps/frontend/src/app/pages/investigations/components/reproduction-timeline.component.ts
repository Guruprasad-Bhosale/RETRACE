import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReproductionResult, ReproductionStep } from '../../../core/models/investigation.models';
import { StatusBadgeComponent } from './status-badge.component';

@Component({
  selector: 'app-reproduction-timeline',
  standalone: true,
  imports: [CommonModule, StatusBadgeComponent],
  template: `
    <div class="space-y-6">
      <!-- Reproduction Header Card -->
      <div class="p-5 rounded-xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div class="space-y-1">
          <div class="flex items-center gap-3">
            <h3 class="text-base font-bold text-slate-100">Deterministic Replay Execution</h3>
            <app-status-badge [status]="reproduction?.status || 'NOT_ATTEMPTED'"></app-status-badge>
          </div>
          <p class="text-xs text-slate-400">
            Reconstructed minimal causal path verifying regression in fresh browser context.
          </p>
        </div>

        <div class="flex items-center gap-4 text-xs font-mono">
          <div class="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-center">
            <span class="block text-slate-500 text-[10px]">STRATEGY</span>
            <span class="font-bold text-slate-200">{{ reproduction?.strategy || 'DIRECT_REPLAY' }}</span>
          </div>
          <div class="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-center">
            <span class="block text-slate-500 text-[10px]">TOTAL DURATION</span>
            <span class="font-bold text-slate-200">{{ formatDuration(reproduction?.total_duration_ms) }}</span>
          </div>
          <div class="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-center">
            <span class="block text-slate-500 text-[10px]">ATTEMPTS</span>
            <span class="font-bold text-slate-200">{{ reproduction?.attempts?.length || 0 }}</span>
          </div>
        </div>
      </div>

      <!-- Verification Notes if available -->
      <div
        *ngIf="reproduction?.final_verification"
        class="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs flex items-start gap-3"
      >
        <span class="text-base">🔍</span>
        <div>
          <span class="font-bold text-slate-200 block">Verification Match: {{ reproduction?.final_verification?.match_status }}</span>
          <span class="text-slate-400">{{ reproduction?.final_verification?.notes || 'Empirical evidence matches expected regression profile.' }}</span>
        </div>
      </div>

      <!-- Causal Replay Step Timeline -->
      <div class="space-y-3">
        <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider">
          Causal Replay Sequence ({{ reproduction?.path?.steps?.length || 0 }} Steps)
        </h4>

        <div *ngIf="!reproduction?.path?.steps?.length" class="p-6 rounded-xl bg-slate-900/40 border border-slate-800 text-center text-slate-500 text-xs">
          No causal reproduction action steps available.
        </div>

        <div class="space-y-2.5">
          <div
            *ngFor="let step of reproduction?.path?.steps || []; let idx = index"
            class="p-3.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 flex items-center justify-between gap-4 transition"
          >
            <!-- Step index and Action Type -->
            <div class="flex items-center gap-3">
              <span class="h-6 w-6 rounded-full bg-slate-950 border border-slate-700 flex items-center justify-center font-mono text-xs font-bold text-slate-300">
                {{ idx + 1 }}
              </span>
              <span
                class="px-2 py-0.5 rounded text-xs font-mono font-bold uppercase"
                [ngClass]="getActionClass(step.action_type)"
              >
                {{ step.action_type }}
              </span>
            </div>

            <!-- Target / Target strategy -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm font-semibold text-slate-200 truncate">
                  {{ step.accessible_name || step.stable_target_identity || step.raw_target || 'Target Window' }}
                </span>
                <span *ngIf="step.target_role" class="px-1.5 py-0.5 rounded bg-slate-950 text-[10px] font-mono text-slate-400 border border-slate-800">
                  role: {{ step.target_role }}
                </span>
              </div>
              <div class="text-xs font-mono text-slate-500 truncate mt-0.5">
                Strategy: {{ step.target_strategy }} • Locator: {{ step.stable_target_identity || step.raw_target || '-' }}
              </div>
            </div>

            <!-- Value / Input -->
            <div *ngIf="step.value" class="px-3 py-1 rounded bg-slate-950 text-xs font-mono text-indigo-300 border border-slate-800">
              Value: "{{ step.value }}"
            </div>

            <!-- Timeout -->
            <div class="text-[11px] font-mono text-slate-500">
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
    if (act.includes('NAVIGAT')) return 'bg-blue-950 text-blue-300 border border-blue-800';
    if (act.includes('CLICK')) return 'bg-emerald-950 text-emerald-300 border border-emerald-800';
    if (act.includes('TYPE')) return 'bg-amber-950 text-amber-300 border border-amber-800';
    if (act.includes('WAIT')) return 'bg-purple-950 text-purple-300 border border-purple-800';
    return 'bg-slate-950 text-slate-300 border border-slate-800';
  }
}
