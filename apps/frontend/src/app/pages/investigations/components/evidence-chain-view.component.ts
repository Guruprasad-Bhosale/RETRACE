import { Component, Input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EvidenceChain, EvidenceChainNode } from '../../../core/models/investigation.models';
import { StatusBadgeComponent } from './status-badge.component';

@Component({
  selector: 'app-evidence-chain-view',
  standalone: true,
  imports: [CommonModule, StatusBadgeComponent],
  template: `
    <div class="space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-base font-semibold text-slate-100 flex items-center gap-2">
            <span class="text-indigo-400 font-mono">⛓</span>
            Unbroken Causal Evidence Chain
          </h3>
          <p class="text-xs text-slate-400 mt-0.5">
            Verifiable progression connecting raw browser observations to localized source code and attributed commits.
          </p>
        </div>
        <div class="text-xs font-mono text-slate-500">
          Chain ID: <span class="text-slate-300">{{ evidenceChain?.chain_id || 'N/A' }}</span>
        </div>
      </div>

      <!-- Chain Nodes Flow -->
      <div class="relative border-l-2 border-indigo-900/60 ml-4 space-y-6 pl-6 py-2">
        <div
          *ngFor="let node of evidenceChain?.nodes || []; let idx = index"
          class="relative group"
        >
          <!-- Timeline Indicator Dot -->
          <div
            class="absolute -left-[31px] top-3.5 h-4 w-4 rounded-full border-2 border-slate-950 flex items-center justify-center transition"
            [ngClass]="selectedNode()?.node_id === node.node_id ? 'bg-indigo-500 ring-4 ring-indigo-500/20' : 'bg-slate-800 group-hover:bg-indigo-600'"
          >
            <span class="h-1.5 w-1.5 rounded-full bg-white"></span>
          </div>

          <!-- Node Card -->
          <div
            (click)="selectNode(node)"
            class="p-4 rounded-xl border transition cursor-pointer"
            [ngClass]="selectedNode()?.node_id === node.node_id ? 'bg-slate-900 border-indigo-500/70 shadow-lg shadow-indigo-950/40' : 'bg-slate-900/70 border-slate-800 hover:border-slate-700 hover:bg-slate-900'"
          >
            <div class="flex items-start justify-between gap-4">
              <div class="space-y-1">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-mono font-semibold text-indigo-400 uppercase tracking-wider">
                    {{ node.phase_origin }}
                  </span>
                  <span class="text-slate-600">•</span>
                  <span class="text-xs font-mono text-slate-500">Node {{ idx + 1 }}</span>
                </div>
                <h4 class="text-sm font-bold text-slate-200">{{ node.title }}</h4>
              </div>
              <app-status-badge [status]="node.status"></app-status-badge>
            </div>

            <p class="text-xs text-slate-300 mt-2 leading-relaxed">
              {{ node.summary }}
            </p>

            <!-- Evidence References Badges -->
            <div *ngIf="node.evidence_ids.length > 0" class="mt-3 flex flex-wrap gap-1.5">
              <span
                *ngFor="let eid of node.evidence_ids"
                class="px-2 py-0.5 rounded bg-slate-950 text-[11px] font-mono text-slate-400 border border-slate-800"
              >
                Ref: {{ eid }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Selected Node Detail Popout -->
      <div *ngIf="selectedNode()" class="p-4 rounded-xl bg-slate-900 border border-indigo-500/40 mt-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
          <div class="flex items-center gap-2">
            <span class="text-xs font-mono text-indigo-400 font-bold">NODE DETAILS:</span>
            <span class="text-sm font-semibold text-white">{{ selectedNode()?.title }}</span>
          </div>
          <button
            (click)="selectedNode.set(null)"
            class="text-xs text-slate-500 hover:text-slate-300 font-mono"
          >
            ✕ Close
          </button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div>
            <span class="text-slate-500 block">Node ID:</span>
            <span class="font-mono text-slate-200">{{ selectedNode()?.node_id }}</span>
          </div>
          <div>
            <span class="text-slate-500 block">Phase Origin:</span>
            <span class="font-mono text-slate-200">{{ selectedNode()?.phase_origin }}</span>
          </div>
        </div>
        <div class="mt-3" *ngIf="hasDetails(selectedNode()?.details)">
          <span class="text-slate-500 text-xs block mb-1">Structured Attributes:</span>
          <pre class="p-3 rounded-lg bg-slate-950 font-mono text-xs text-slate-300 overflow-x-auto border border-slate-800">{{ selectedNode()?.details | json }}</pre>
        </div>
      </div>
    </div>
  `,
})
export class EvidenceChainViewComponent {
  @Input() evidenceChain: EvidenceChain | null = null;
  readonly selectedNode = signal<EvidenceChainNode | null>(null);

  selectNode(node: EvidenceChainNode): void {
    if (this.selectedNode()?.node_id === node.node_id) {
      this.selectedNode.set(null);
    } else {
      this.selectedNode.set(node);
    }
  }

  hasDetails(details?: Record<string, unknown>): boolean {
    return !!details && Object.keys(details).length > 0;
  }
}
