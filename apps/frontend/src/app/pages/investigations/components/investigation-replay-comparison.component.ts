import { Component, Input, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  InvestigationComparisonResult,
  InvestigationSummaryItem,
  ReplayResult,
} from '../../../core/models/investigation.models';
import { InvestigationService } from '../../../core/services/investigation.service';
import { ForensicInteractionService } from '../../../core/services/forensic-interaction.service';

@Component({
  selector: 'app-investigation-replay-comparison',
  standalone: true,
  imports: [CommonModule, FormsModule],
  styles: [':host { display: block; }'],
  template: `

    <div class="space-y-6 font-mono">
      <!-- 1. Offline Deterministic Replay Header & Controls -->
      <div class="bento-card p-5 border border-(--grid) space-y-4">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xs tracking-wider uppercase text-(--or) font-bold">Phase 19 Replay</span>
              <span class="text-xs text-(--muted)">&bull;</span>
              <span class="text-xs text-(--muted)">Deterministic Verification Engine</span>
            </div>
            <h3 class="text-base font-bold text-(--ink) mt-1 uppercase">Forensic Replay & Recomputation</h3>
            <p class="text-xs text-(--muted) mt-0.5">
              Recomputes evidence graph, hypotheses, and root cause offline over captured immutable snapshots without live browser execution.
            </p>
          </div>

          <!-- Replay Actions -->
          <div class="flex items-center gap-2">
            <button
              type="button"
              (click)="triggerReplay()"
              [disabled]="isReplaying()"
              class="btn-retrace text-xs py-2 px-4"
            >
              <span *ngIf="isReplaying()" class="animate-spin text-sm">&circlearrowright;</span>
              <span>{{ isReplaying() ? 'REPLAYING EVIDENCE...' : '▶ RUN FORENSIC REPLAY' }}</span>
            </button>
          </div>
        </div>

        <!-- Replay Result Outcome -->
        <div *ngIf="replayResult()" class="mt-5 pt-4 border-t border-(--grid) space-y-4 animate-reveal">
          <div class="flex flex-wrap items-center gap-3">
            <span
              class="px-2.5 py-1 text-xs font-bold rounded uppercase tracking-wider"
              [ngClass]="{
                'bg-emerald-950 text-emerald-400 border border-emerald-800': replayResult()?.is_reproducible,
                'bg-rose-950 text-rose-400 border border-rose-800': !replayResult()?.is_reproducible
              }"
            >
              {{ replayResult()?.status }}
            </span>
            <span class="text-xs text-(--muted)">
              Replay ID: <strong class="text-(--ink)">{{ replayResult()?.replay_id }}</strong>
            </span>
            <span class="text-xs text-(--muted)">
              Engine Version: <strong class="text-(--ink)">{{ replayResult()?.analysis_version }}</strong>
            </span>
          </div>

          <!-- Canonical Hashes Verification Grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            <div class="bento-card-elevated border border-(--grid) p-3 rounded">
              <div class="text-(--muted) text-[10px] uppercase">Snapshot Hash</div>
              <div class="text-(--ink) truncate mt-1 font-bold" [title]="replayResult()?.snapshot_hash">
                {{ replayResult()?.snapshot_hash | slice: 0 : 16 }}...
              </div>
            </div>
            <div class="bento-card-elevated border border-(--grid) p-3 rounded">
              <div class="text-(--muted) text-[10px] uppercase">Graph Topology Hash</div>
              <div class="text-(--ink) truncate mt-1 font-bold" [title]="replayResult()?.graph_hash">
                {{ replayResult()?.graph_hash | slice: 0 : 16 }}...
              </div>
            </div>
            <div class="bento-card-elevated border border-(--grid) p-3 rounded">
              <div class="text-(--muted) text-[10px] uppercase">Hypothesis Set Hash</div>
              <div class="text-(--ink) truncate mt-1 font-bold" [title]="replayResult()?.hypothesis_hash">
                {{ replayResult()?.hypothesis_hash | slice: 0 : 16 }}...
              </div>
            </div>
            <div class="bento-card-elevated border border-(--grid) p-3 rounded">
              <div class="text-(--muted) text-[10px] uppercase">Explanation Hash</div>
              <div class="text-(--ink) truncate mt-1 font-bold" [title]="replayResult()?.explanation_hash">
                {{ replayResult()?.explanation_hash | slice: 0 : 16 }}...
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. Multi-Investigation Forensic Comparison -->
      <div class="bento-card p-5 border border-(--grid) space-y-4">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xs tracking-wider uppercase text-blue-500 font-bold">Investigation Diff</span>
              <span class="text-xs text-(--muted)">&bull;</span>
              <span class="text-xs text-(--muted)">Comparative Graph & Root Cause Analyzer</span>
            </div>
            <h3 class="text-base font-bold text-(--ink) mt-1 uppercase">Cross-Investigation Differential</h3>
            <p class="text-xs text-(--muted) mt-0.5">
              Analyze shared vs unique evidence items, topological graph differences, and root-cause divergences against another investigation.
            </p>
          </div>

          <div class="flex items-center gap-2">
            <select
              [(ngModel)]="selectedOtherId"
              class="bg-(--surface) border border-(--grid) text-(--ink) text-xs px-3 py-2 rounded focus:outline-none focus:border-(--or)"
            >
              <option value="" disabled selected>Select comparison target...</option>
              <option *ngFor="let item of otherInvestigations()" [value]="item.investigation_id">
                {{ item.investigation_id }} — {{ item.title | slice: 0 : 32 }}
              </option>
            </select>
            <button
              type="button"
              (click)="triggerComparison()"
              [disabled]="!selectedOtherId || isComparing()"
              class="btn-retrace text-xs py-2 px-3"
            >
              COMPARE
            </button>
          </div>
        </div>

        <!-- Comparison Results Breakdown -->
        <div *ngIf="comparisonResult()" class="mt-5 pt-4 border-t border-(--grid) space-y-4 animate-reveal">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div class="bento-card-elevated border border-(--grid) p-3 rounded">
              <div class="text-(--muted) text-[10px] uppercase">Shared Evidence</div>
              <div class="text-(--ink) font-bold text-sm mt-1">{{ comparisonResult()?.shared_evidence_count }} items</div>
            </div>
            <div class="bento-card-elevated border border-(--grid) p-3 rounded">
              <div class="text-(--muted) text-[10px] uppercase">Unique to Inv A</div>
              <div class="text-(--ink) font-bold text-sm mt-1">{{ comparisonResult()?.unique_evidence_a_count }} items</div>
            </div>
            <div class="bento-card-elevated border border-(--grid) p-3 rounded">
              <div class="text-(--muted) text-[10px] uppercase">Unique to Inv B</div>
              <div class="text-(--ink) font-bold text-sm mt-1">{{ comparisonResult()?.unique_evidence_b_count }} items</div>
            </div>
            <div class="bento-card-elevated border border-(--grid) p-3 rounded">
              <div class="text-(--muted) text-[10px] uppercase">Root Cause Match</div>
              <div class="font-bold text-sm mt-1" [ngClass]="comparisonResult()?.root_cause_matches ? 'text-emerald-500' : 'text-amber-500'">
                {{ comparisonResult()?.root_cause_matches ? 'MATCHING' : 'DIVERGED' }}
              </div>
            </div>
          </div>

          <!-- Graph Diff Changes List -->
          <div *ngIf="comparisonResult()?.graph_diff?.length" class="space-y-2">
            <div class="text-xs text-(--muted) uppercase tracking-wider font-bold">
              Topological Graph Differences ({{ comparisonResult()?.graph_diff?.length }})
            </div>
            <div class="space-y-2">
              <div
                *ngFor="let diff of comparisonResult()?.graph_diff"
                class="bento-card-elevated border border-(--grid) rounded p-3 text-xs flex items-start gap-3"
              >
                <span
                  class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider"
                  [ngClass]="{
                    'bg-amber-950 text-amber-400 border border-amber-800': diff.diff_type === 'CHANGED_ROOT_CAUSE',
                    'bg-blue-950 text-blue-400 border border-blue-800': diff.diff_type === 'ADDED_NODE' || diff.diff_type === 'REMOVED_NODE',
                    'bg-stone-900 text-stone-400 border border-stone-800': diff.diff_type === 'CHANGED_EDGE' || diff.diff_type === 'CHANGED_STATE'
                  }"
                >
                  {{ diff.diff_type }}
                </span>
                <div class="flex-1">
                  <div class="text-(--ink) font-medium">{{ diff.details }}</div>
                  <div class="text-[10px] text-(--muted) mt-0.5">Target: {{ diff.node_or_edge_id }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class InvestigationReplayComparisonComponent implements OnInit {
  @Input() investigationId = '';

  private readonly investigationService = inject(InvestigationService);
  readonly forensic = inject(ForensicInteractionService);

  readonly replayResult = signal<ReplayResult | null>(null);
  readonly comparisonResult = signal<InvestigationComparisonResult | null>(null);
  readonly isReplaying = signal<boolean>(false);
  readonly isComparing = signal<boolean>(false);
  readonly otherInvestigations = signal<InvestigationSummaryItem[]>([]);

  selectedOtherId = '';

  ngOnInit(): void {
    this.investigationService.loadInvestigations().subscribe((items) => {
      this.otherInvestigations.set(items.filter((i) => i.investigation_id !== this.investigationId));
    });
  }

  triggerReplay(): void {
    if (!this.investigationId) return;
    this.isReplaying.set(true);
    this.investigationService.replayInvestigation(this.investigationId).subscribe({
      next: (res) => {
        this.replayResult.set(res);
        this.isReplaying.set(false);
      },
      error: () => {
        this.isReplaying.set(false);
      },
    });
  }

  triggerComparison(): void {
    if (!this.investigationId || !this.selectedOtherId) return;
    this.isComparing.set(true);
    this.investigationService.compareInvestigations(this.investigationId, this.selectedOtherId).subscribe({
      next: (res) => {
        this.comparisonResult.set(res);
        this.isComparing.set(false);
      },
      error: () => {
        this.isComparing.set(false);
      },
    });
  }
}
