import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  imports: [CommonModule],
  template: `
    <span
      class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide border uppercase"
      [ngClass]="badgeClass"
      [attr.aria-label]="statusText"
    >
      <span class="h-1.5 w-1.5 rounded-full" [ngClass]="dotClass"></span>
      <span>{{ statusText }}</span>
    </span>
  `,
})
export class StatusBadgeComponent {
  @Input() status = '';
  @Input() type: 'investigation' | 'rootcause' | 'test' | 'category' = 'investigation';

  get statusText(): string {
    return this.status || 'UNKNOWN';
  }

  get badgeClass(): string {
    const s = this.status.toUpperCase();
    if (s === 'COMPLETED' || s === 'LOCATED' || s === 'VALIDATED' || s === 'REPRODUCED') {
      return 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80';
    }
    if (s === 'PARTIAL' || s === 'PARTIALLY_LOCATED' || s === 'CANDIDATE_ONLY' || s === 'STRUCTURALLY_VALIDATED' || s === 'PARTIALLY_SYNTHESIZED') {
      return 'bg-amber-950/80 text-amber-300 border-amber-800/80';
    }
    if (s === 'INCONCLUSIVE' || s === 'INCOMPLETE') {
      return 'bg-purple-950/80 text-purple-300 border-purple-800/80';
    }
    if (s === 'FAILED' || s === 'VALIDATION_FAILED' || s === 'NOT_REPRODUCED') {
      return 'bg-rose-950/80 text-rose-300 border-rose-800/80';
    }
    if (s === 'UNSUPPORTED' || s === 'NOT_VALIDATED') {
      return 'bg-slate-900 text-slate-400 border-slate-700';
    }
    // Generic category/type
    return 'bg-indigo-950/60 text-indigo-300 border-indigo-800/60';
  }

  get dotClass(): string {
    const s = this.status.toUpperCase();
    if (s === 'COMPLETED' || s === 'LOCATED' || s === 'VALIDATED' || s === 'REPRODUCED') {
      return 'bg-emerald-400';
    }
    if (s === 'PARTIAL' || s === 'PARTIALLY_LOCATED' || s === 'CANDIDATE_ONLY' || s === 'STRUCTURALLY_VALIDATED' || s === 'PARTIALLY_SYNTHESIZED') {
      return 'bg-amber-400';
    }
    if (s === 'INCONCLUSIVE' || s === 'INCOMPLETE') {
      return 'bg-purple-400';
    }
    if (s === 'FAILED' || s === 'VALIDATION_FAILED' || s === 'NOT_REPRODUCED') {
      return 'bg-rose-400';
    }
    return 'bg-slate-400';
  }
}
