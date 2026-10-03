import { Component, Input, inject, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  EvidenceGraph,
  EvidenceGraphNode,
  EvidenceGraphEdge,
  ForensicInvestigationExplanation,
  InvestigationResult,
} from '../../../core/models/investigation.models';
import { ForensicInteractionService } from '../../../core/services/forensic-interaction.service';

@Component({
  selector: 'app-evidence-graph-view',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="bento-card p-5 md:p-6 border border-(--grid) bg-(--surface) relative focus-reveal font-mono" tabindex="0" (keydown)="handleKeyDown($event)">
      <!-- Section Header with Follow Evidence Controls -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5 pb-3 border-b border-(--grid)">
        <div class="flex items-center space-x-3">
          <div class="w-2.5 h-2.5 rounded-full bg-(--or) animate-pulse"></div>
          <div>
            <div class="flex items-center gap-2">
              <h3 class="text-sm font-black uppercase tracking-wider text-(--ink)">
                Forensic Evidence DAG
              </h3>
              <span class="px-1.5 py-0.5 rounded text-[9px] bg-(--elevated) border border-(--grid) text-(--or) font-bold">
                TOPOLOGY
              </span>
            </div>
            <p class="text-xs text-(--muted) mt-0.5">
              Causal DAG linking multi-phase observations to source AST diffs
            </p>
          </div>
        </div>

        <!-- Follow Evidence Action Toolbar -->
        <div class="flex items-center flex-wrap gap-2">
          <!-- Graph Badges -->
          <div class="hidden sm:flex items-center space-x-2 mr-2">
            <span class="px-2 py-0.5 rounded bg-(--elevated) border border-(--grid) text-[10px] text-(--muted)">
              {{ graph?.nodes?.length || 0 }} NODES
            </span>
            <span class="px-2 py-0.5 rounded bg-(--elevated) border border-(--grid) text-[10px] text-(--muted)">
              {{ graph?.edges?.length || 0 }} EDGES
            </span>
          </div>

          <!-- FOLLOW EVIDENCE Playback Trigger -->
          <div class="flex items-center gap-1.5 bg-(--elevated) border border-(--grid) p-1 rounded">
            <button
              *ngIf="!forensic.isPathModeActive()"
              (click)="startFollowEvidence()"
              class="btn-retrace text-[10px] py-1 px-3 cursor-pointer"
              aria-label="Start Follow Evidence playback"
            >
              FOLLOW EVIDENCE &rarr;
            </button>

            <ng-container *ngIf="forensic.isPathModeActive()">
              <button
                (click)="forensic.isPathPlaying() ? forensic.pauseEvidencePath() : forensic.resumeEvidencePath(graph, investigation, explanation)"
                class="px-2.5 py-1 rounded bg-(--or) text-stone-900 font-bold text-[10px] hover:opacity-90 transition cursor-pointer"
                [attr.aria-label]="forensic.isPathPlaying() ? 'Pause evidence playback' : 'Play evidence playback'"
              >
                {{ forensic.isPathPlaying() ? '❚❚ PAUSE' : '▶ PLAY' }}
              </button>

              <button
                (click)="forensic.previousEvidencePathStep(graph, investigation, explanation)"
                [disabled]="forensic.currentPathStep() === 0"
                class="px-2 py-1 rounded hover:bg-(--surface) border border-(--grid) text-[10px] disabled:opacity-30 cursor-pointer"
                title="Previous step"
              >
                &larr;
              </button>

              <button
                (click)="forensic.skipEvidencePath(graph, investigation, explanation)"
                [disabled]="forensic.currentPathStep() >= forensic.pathSteps.length - 1"
                class="px-2 py-1 rounded hover:bg-(--surface) border border-(--grid) text-[10px] disabled:opacity-30 cursor-pointer"
                title="Skip to next step"
              >
                &rarr;
              </button>

              <button
                (click)="forensic.togglePlaybackSpeed()"
                class="px-2 py-1 rounded hover:bg-(--surface) border border-(--grid) text-[10px] font-bold text-(--or) cursor-pointer"
                title="Toggle playback speed"
              >
                {{ forensic.playbackSpeed() }}&times;
              </button>

              <button
                (click)="forensic.exitEvidencePath()"
                class="px-2 py-1 rounded hover:bg-(--surface) text-[10px] text-(--muted) hover:text-red-500 cursor-pointer"
                title="Exit playback"
              >
                &times; EXIT
              </button>
            </ng-container>
          </div>
        </div>
      </div>

      <!-- Evidence Path Step Illuminator Indicator Bar -->
      <div *ngIf="forensic.isPathModeActive()" class="mb-4 p-3 rounded bento-card-elevated border-l-4 border-l-(--or) space-y-1">
        <div class="flex items-center justify-between text-xs">
          <span class="font-bold text-(--or) uppercase tracking-wider">
            STEP 0{{ forensic.currentPathStep() + 1 }}: {{ forensic.pathSteps[forensic.currentPathStep()].label }}
          </span>
          <span class="text-[10px] text-(--muted)">
            STAGE: {{ forensic.pathSteps[forensic.currentPathStep()].stage }} ({{ forensic.currentPathStep() + 1 }}/{{ forensic.pathSteps.length }})
          </span>
        </div>
        <p class="text-[11px] text-(--ink) leading-relaxed">
          {{ forensic.pathSteps[forensic.currentPathStep()].description }}
        </p>
      </div>

      <!-- Desktop / Tablet Interactive DAG Nodes Surface -->
      <div *ngIf="graph && graph.nodes && graph.nodes.length > 0; else noGraph" class="relative">
        
        <!-- 1. Compact High-Signal Node Cards (Desktop & Tablet) -->
        <div class="hidden sm:grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-5">
          <div
            *ngFor="let node of graph.nodes; let i = index"
            (click)="onNodeClick(node)"
            (mouseenter)="onNodeHover(node.node_id)"
            (mouseleave)="onNodeHover(null)"
            tabindex="0"
            role="button"
            [attr.aria-label]="'Evidence node ' + node.title + ', status ' + node.status"
            [attr.aria-selected]="forensic.selectedEvidenceId() === node.node_id"
            class="p-3 rounded border bento-card-elevated cursor-pointer transition-all duration-200 flex flex-col justify-between relative group"
            [ngClass]="getNodeCardClasses(node.node_id)"
          >
            <!-- Step Counter & Node Type -->
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-[9px] font-bold" [ngClass]="forensic.selectedEvidenceId() === node.node_id ? 'text-(--or)' : 'text-(--muted)'">
                #0{{ i + 1 }}
              </span>
              <span
                class="px-1.5 py-0.2 rounded text-[8px] uppercase font-bold"
                [ngClass]="getNodeTypeBadgeClass(node.node_type)"
              >
                {{ node.node_type }}
              </span>
            </div>

            <!-- Title -->
            <p class="text-xs font-bold text-(--ink) line-clamp-2 mb-2 leading-snug">
              {{ node.title }}
            </p>

            <!-- Status & Confidence -->
            <div class="flex items-center justify-between pt-1.5 border-t border-(--grid) text-[9px]">
              <span class="text-(--muted) uppercase">{{ node.status }}</span>
              <span class="text-(--or) font-bold">{{ (node.confidence_score * 100).toFixed(0) }}%</span>
            </div>
          </div>
        </div>

        <!-- 2. Mobile Linear Forensic Chain (OBSERVATION ↓ DIFF ↓ HYPOTHESIS ↓ SOURCE ↓ ROOT CAUSE) -->
        <div class="sm:hidden space-y-2 mb-5">
          <div class="text-[9px] uppercase font-bold text-(--or) tracking-wider mb-2">
            LINEAR FORENSIC DAG PATH
          </div>
          <div
            *ngFor="let node of graph.nodes; let i = index; let isLast = last"
            class="flex flex-col items-center"
          >
            <div
              (click)="onNodeClick(node)"
              tabindex="0"
              role="button"
              class="w-full p-3 rounded bento-card-elevated border cursor-pointer transition"
              [ngClass]="getNodeCardClasses(node.node_id)"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="text-[9px] font-bold text-(--or)">#0{{ i + 1 }} {{ node.node_type }}</span>
                <span class="text-[9px] text-(--muted)">{{ (node.confidence_score * 100).toFixed(0) }}%</span>
              </div>
              <div class="text-xs font-bold text-(--ink)">{{ node.title }}</div>
            </div>
            <!-- Vertical Arrow Flow -->
            <div *ngIf="!isLast" class="py-0.5 text-(--or) font-bold text-xs select-none">
              &darr;
            </div>
          </div>
        </div>

        <!-- 3. Semantic Causal Relationships (Compact Table) -->
        <div class="p-3.5 rounded bento-card-elevated border border-(--grid)">
          <div class="flex items-center justify-between mb-2">
            <h4 class="text-xs uppercase font-bold text-(--ink) flex items-center gap-2">
              <span class="w-1.5 h-1.5 bg-(--or) rounded-full"></span>
              Causal Edges ({{ graph.edges.length }})
            </h4>
            <span class="text-[9px] text-(--muted)">CLICK NODE ABOVE FOR FULL DETAILS</span>
          </div>

          <div class="space-y-1.5">
            <div
              *ngFor="let edge of graph.edges"
              class="flex flex-col sm:flex-row sm:items-center justify-between p-2 rounded border text-xs transition"
              [ngClass]="getEdgeRowClasses(edge)"
            >
              <div class="flex items-center space-x-2 truncate">
                <span class="px-1.5 py-0.2 rounded text-[9px] font-bold bg-(--surface) text-(--or) border border-(--grid)">
                  {{ edge.relationship }}
                </span>
                <span class="text-(--ink) font-bold truncate">
                  {{ getNodeTitle(edge.source_node_id) }} &rarr; {{ getNodeTitle(edge.target_node_id) }}
                </span>
              </div>
              <div class="flex items-center space-x-2 text-[10px] text-(--muted) mt-1 sm:mt-0">
                <span class="text-(--ink) font-bold">Weight: {{ edge.weight }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 4. Selected Node Inspector Drawer (Progressive Disclosure) -->
        <div
          *ngIf="selectedNodeDetails"
          class="mt-4 p-4 rounded bento-card-elevated border-2 border-(--or) shadow-md animate-reveal space-y-3"
        >
          <div class="flex items-center justify-between pb-2 border-b border-(--grid)">
            <div class="flex items-center space-x-2">
              <span class="px-2 py-0.5 rounded text-[9px] uppercase font-bold" [ngClass]="getNodeTypeBadgeClass(selectedNodeDetails.node_type)">
                {{ selectedNodeDetails.node_type }}
              </span>
              <h4 class="text-xs font-bold text-(--ink)">
                {{ selectedNodeDetails.title }}
              </h4>
            </div>
            <button
              (click)="forensic.clearSelection()"
              class="text-xs text-(--muted) hover:text-(--or) transition cursor-pointer"
              aria-label="Close node inspector"
            >
              [CLOSE &times;]
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div>
              <span class="text-(--muted) block text-[9px] uppercase">Node Identifier</span>
              <span class="text-(--ink) font-bold text-xs">{{ selectedNodeDetails.node_id }}</span>
            </div>
            <div>
              <span class="text-(--muted) block text-[9px] uppercase">Confidence Score</span>
              <span class="text-emerald-500 font-bold text-xs">{{ (selectedNodeDetails.confidence_score * 100).toFixed(0) }}% Verified</span>
            </div>
            <div>
              <span class="text-(--muted) block text-[9px] uppercase">Evaluation Status</span>
              <span class="text-(--ink) font-bold text-xs">{{ selectedNodeDetails.status }}</span>
            </div>
          </div>

          <div *ngIf="selectedNodeDetails.metadata" class="pt-2 border-t border-(--grid) text-xs">
            <span class="text-(--muted) block text-[9px] uppercase mb-1">Causal Metadata:</span>
            <pre class="p-2 rounded bg-(--surface) text-[10px] text-(--muted) overflow-x-auto">{{ selectedNodeDetails.metadata | json }}</pre>
          </div>
        </div>
      </div>

      <ng-template #noGraph>
        <div class="p-8 text-center text-xs text-(--muted)">
          No evidence graph nodes generated for this investigation.
        </div>
      </ng-template>
    </div>
  `,
})
export class EvidenceGraphViewComponent {
  @Input() graph: EvidenceGraph | null = null;
  @Input() investigation: InvestigationResult | null = null;
  @Input() explanation: ForensicInvestigationExplanation | null = null;

  readonly forensic = inject(ForensicInteractionService);

  get selectedNodeDetails(): EvidenceGraphNode | null {
    const selectedId = this.forensic.selectedEvidenceId();
    if (!selectedId || !this.graph?.nodes) return null;
    return this.graph.nodes.find((n) => n.node_id === selectedId) || null;
  }

  startFollowEvidence(): void {
    if (this.graph) {
      this.forensic.startEvidencePath(this.graph, this.investigation, this.explanation);
    }
  }

  onNodeClick(node: EvidenceGraphNode): void {
    if (this.forensic.selectedEvidenceId() === node.node_id) {
      this.forensic.clearSelection();
    } else {
      this.forensic.selectEvidenceNode(node, this.graph, this.investigation, this.explanation);
    }
  }

  onNodeHover(nodeId: string | null): void {
    this.forensic.hoverEvidenceNode(nodeId, this.graph);
  }

  getNodeTitle(nodeId: string): string {
    const node = this.graph?.nodes.find((n) => n.node_id === nodeId);
    return node ? node.title : nodeId;
  }

  getNodeCardClasses(nodeId: string): string {
    const isSelected = this.forensic.selectedEvidenceId() === nodeId;
    const isHovered = this.forensic.hoveredEvidenceId() === nodeId;

    if (isSelected) {
      return 'border-(--or) ring-2 ring-(--or) shadow-md bg-(--elevated) forensic-pulse';
    }
    if (isHovered) {
      return 'border-(--or) bg-(--elevated)';
    }
    return 'border-(--grid) hover:border-(--gs)';
  }

  getEdgeRowClasses(edge: EvidenceGraphEdge): string {
    const isSourceSelected = this.forensic.selectedEvidenceId() === edge.source_node_id;
    const isTargetSelected = this.forensic.selectedEvidenceId() === edge.target_node_id;

    if (isSourceSelected || isTargetSelected) {
      return 'border-(--or) bg-orange-500/10';
    }
    return 'border-(--grid) bg-(--elevated)';
  }

  getNodeTypeBadgeClass(nodeType: string): string {
    switch (nodeType) {
      case 'OBSERVATION':
        return 'bg-blue-500/10 text-blue-500 border border-blue-500/30';
      case 'DIFF':
        return 'bg-amber-500/10 text-amber-500 border border-amber-500/30';
      case 'HYPOTHESIS':
        return 'bg-purple-500/10 text-purple-500 border border-purple-500/30';
      case 'SOURCE':
        return 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/30';
      case 'ROOT_CAUSE':
        return 'bg-rose-500/10 text-rose-500 border border-rose-500/30';
      case 'REPRODUCTION':
        return 'bg-orange-500/10 text-(--or) border border-orange-500/30';
      default:
        return 'bg-stone-500/10 text-stone-400 border border-stone-500/30';
    }
  }

  @HostListener('keydown', ['$event'])
  handleKeyDown(e: KeyboardEvent): void {
    if (!this.graph?.nodes?.length) return;
    const currentId = this.forensic.selectedEvidenceId();
    const idx = this.graph.nodes.findIndex((n) => n.node_id === currentId);

    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      const nextIdx = idx === -1 ? 0 : Math.min(idx + 1, this.graph.nodes.length - 1);
      this.onNodeClick(this.graph.nodes[nextIdx]);
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      const prevIdx = idx === -1 ? 0 : Math.max(idx - 1, 0);
      this.onNodeClick(this.graph.nodes[prevIdx]);
    } else if (e.key === 'Escape') {
      this.forensic.clearSelection();
    }
  }
}
