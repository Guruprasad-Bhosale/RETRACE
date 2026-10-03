import { Component, Input, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ForensicInvestigationExplanation,
  AlternativeExplanation,
  EvidenceGraph,
} from '../../../core/models/investigation.models';
import { ForensicInteractionService } from '../../../core/services/forensic-interaction.service';

@Component({
  selector: 'app-hypotheses-view',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="space-y-5 font-mono">
      <!-- 1. Primary Confirmed Hypothesis -->
      <div
        class="bento-card p-5 border transition-all duration-300 cursor-pointer"
        [ngClass]="getHypothesisCardClasses(explanation?.primary_hypothesis?.hypothesis_id || 'primary')"
        (click)="onHypothesisClick(explanation?.primary_hypothesis?.hypothesis_id || 'primary')"
        tabindex="0"
        role="button"
        [attr.aria-label]="'Primary hypothesis: ' + (explanation?.primary_hypothesis?.title || 'Root Cause Hypothesis')"
      >
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3 pb-3 border-b border-(--grid)">
          <div class="flex items-center space-x-2">
            <span class="px-2 py-0.5 rounded bg-(--or) text-stone-900 text-[10px] font-bold uppercase tracking-wider">
              Primary Hypothesis
            </span>
            <span class="px-1.5 py-0.5 rounded text-[9px] font-bold bento-card-elevated border border-(--grid) text-(--muted)">
              {{ explanation?.primary_hypothesis?.category || 'DIAGNOSTIC' }}
            </span>
          </div>
          <div class="flex items-center space-x-2">
            <span class="text-[10px] text-(--muted)">CONFIDENCE:</span>
            <span class="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/10 text-emerald-500 border border-emerald-500/30">
              {{ explanation?.confidence?.level || 'HIGH' }} ({{ ((explanation?.confidence?.score || 0.95) * 100).toFixed(0) }}%)
            </span>
          </div>
        </div>

        <h3 class="text-sm font-bold text-(--ink) mb-1">
          {{ explanation?.primary_hypothesis?.title || 'Root Cause Hypothesis' }}
        </h3>
        <p class="text-xs text-(--muted) leading-relaxed mb-3">
          {{ explanation?.primary_hypothesis?.description || explanation?.root_cause_summary }}
        </p>

        <div class="grid grid-cols-3 gap-2 p-2.5 rounded bento-card-elevated border border-(--grid) text-xs text-center">
          <div>
            <span class="text-(--muted) block text-[9px] uppercase">Supporting</span>
            <span class="text-(--ink) font-bold text-xs">{{ explanation?.confidence?.supporting_count || 0 }} Sources</span>
          </div>
          <div>
            <span class="text-(--muted) block text-[9px] uppercase">Contradictions</span>
            <span class="text-(--ink) font-bold text-xs">{{ explanation?.confidence?.contradicting_count || 0 }}</span>
          </div>
          <div>
            <span class="text-(--muted) block text-[9px] uppercase">Status</span>
            <span class="text-emerald-500 font-bold text-xs">{{ explanation?.primary_hypothesis?.status || 'CONFIRMED' }}</span>
          </div>
        </div>
      </div>

      <!-- 2. Systematically Eliminated Hypotheses (Progressive Disclosure Accordion) -->
      <div class="bento-card p-5 border border-(--grid) space-y-3">
        <div class="flex items-center justify-between pb-2 border-b border-(--grid)">
          <div class="flex items-center space-x-2">
            <div class="w-2 h-2 rounded-full bg-(--muted)"></div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-(--ink)">
              Eliminated Hypotheses
            </h4>
          </div>
          <span class="px-2 py-0.5 rounded bento-card-elevated border border-(--grid) text-[10px] text-(--muted) font-bold">
            {{ explanation?.eliminated_alternatives?.length || 0 }} RULED OUT
          </span>
        </div>

        <div class="space-y-2">
          @for (alt of explanation?.eliminated_alternatives; track alt.alternative_id) {
            <div
              (click)="toggleAlternative(alt.alternative_id)"
              tabindex="0"
              role="button"
              class="p-3 rounded border bento-card-elevated cursor-pointer transition-all duration-200 space-y-1.5"
              [class.border-(--or)]="expandedAlternativeId() === alt.alternative_id"
              [class.border-(--grid)]="expandedAlternativeId() !== alt.alternative_id"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2 truncate">
                  <span
                    class="px-1.5 py-0.2 rounded text-[8px] font-bold uppercase"
                    [ngClass]="getHypothesisStateBadgeClass(alt.status)"
                  >
                    {{ alt.status }}
                  </span>
                  <span class="text-xs font-bold text-(--ink) truncate">
                    {{ alt.title }}
                  </span>
                </div>
                <span class="text-[10px] text-(--muted) select-none">
                  {{ expandedAlternativeId() === alt.alternative_id ? '▲' : '▼' }}
                </span>
              </div>

              <!-- Expanded Elimination Reason -->
              <div
                *ngIf="expandedAlternativeId() === alt.alternative_id || showAllDetails()"
                class="pt-2 mt-1 border-t border-(--grid) text-[11px] text-(--muted) leading-relaxed animate-reveal"
              >
                <div class="text-[9px] uppercase font-bold text-(--or) mb-0.5">Elimination Rationale:</div>
                {{ alt.elimination_reason }}
              </div>
            </div>
          } @empty {
            <div class="text-xs text-(--muted) p-2 text-center">
              No alternative hypotheses recorded.
            </div>
          }
        </div>
      </div>

      <!-- 3. Falsification Verification Protocol (Collapsible) -->
      @if (explanation?.falsification) {
        <div class="bento-card p-4 border border-(--grid) space-y-2 text-xs">
          <div class="flex items-center justify-between">
            <span class="text-[10px] uppercase font-bold text-amber-500 flex items-center gap-1.5">
              <span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
              Falsification Protocol
            </span>
            <span class="text-[9px] text-(--muted)">{{ explanation?.falsification?.condition_id }}</span>
          </div>
          <p class="text-[11px] text-(--ink) leading-normal">
            {{ explanation?.falsification?.statement }}
          </p>
        </div>
      }
    </div>
  `,
})
export class HypothesesViewComponent {
  @Input() explanation: ForensicInvestigationExplanation | null = null;
  @Input() graph: EvidenceGraph | null = null;

  readonly forensic = inject(ForensicInteractionService);
  readonly expandedAlternativeId = signal<string | null>(null);
  readonly showAllDetails = signal<boolean>(true);

  toggleAlternative(id: string): void {
    if (this.expandedAlternativeId() === id) {
      this.expandedAlternativeId.set(null);
    } else {
      this.expandedAlternativeId.set(id);
      this.forensic.selectHypothesis(id, this.explanation, this.graph);
    }
  }

  onHypothesisClick(hypothesisId: string): void {
    this.forensic.selectHypothesis(hypothesisId, this.explanation, this.graph);
  }

  getHypothesisCardClasses(hypothesisId: string): string {
    const isHighlighted = this.forensic.highlightedHypothesisId() === hypothesisId ||
      (hypothesisId === 'primary' && this.forensic.highlightedHypothesisId() === this.explanation?.primary_hypothesis?.hypothesis_id);
    const isSelected = this.forensic.selectedHypothesisId() === hypothesisId;

    if (isSelected || isHighlighted) {
      return 'border-(--or) ring-2 ring-(--or) shadow-md bg-(--surface) forensic-pulse';
    }
    return 'border-(--grid) hover:border-(--gs)';
  }

  getHypothesisStateBadgeClass(status: string): string {
    switch (status) {
      case 'CONFIRMED':
        return 'bg-emerald-500/15 text-emerald-500 border border-emerald-500/30';
      case 'SUPPORTED':
        return 'bg-blue-500/15 text-blue-500 border border-blue-500/30';
      case 'PROPOSED':
        return 'bg-amber-500/15 text-amber-500 border border-amber-500/30';
      case 'WEAKENED':
        return 'bg-purple-500/15 text-purple-500 border border-purple-500/30';
      case 'ELIMINATED':
        return 'bg-red-500/15 text-red-500 border border-red-500/30';
      case 'CONFLICTED':
        return 'bg-rose-600/15 text-rose-500 border border-rose-600/30';
      default:
        return 'bg-stone-500/15 text-stone-400 border border-stone-500/30';
    }
  }
}
