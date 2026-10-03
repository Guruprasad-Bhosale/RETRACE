import { Injectable, signal, computed } from '@angular/core';
import {
  EvidenceGraph,
  EvidenceGraphNode,
  EvidenceGraphEdge,
  ForensicInvestigationExplanation,
  InvestigationResult,
} from '../models/investigation.models';

export type ForensicTimelineStage =
  | 'OBSERVE'
  | 'ALIGN'
  | 'DIFF'
  | 'CLASSIFY'
  | 'HYPOTHESIZE'
  | 'REPRODUCE'
  | 'LOCALIZE'
  | 'SYNTHESIZE';

export interface SourceFocusLocation {
  filePath: string;
  startLine: number;
  endLine: number;
  symbolName?: string | null;
}

export interface ForensicPathStep {
  stepIndex: number;
  stage: ForensicTimelineStage;
  label: string;
  nodeType: string;
  description: string;
}

@Injectable({
  providedIn: 'root',
})
export class ForensicInteractionService {
  // Selected / Hovered state signals
  readonly selectedEvidenceId = signal<string | null>(null);
  readonly hoveredEvidenceId = signal<string | null>(null);
  readonly selectedHypothesisId = signal<string | null>(null);
  readonly highlightedHypothesisId = signal<string | null>(null);
  readonly focusedSourceLocation = signal<SourceFocusLocation | null>(null);
  readonly highlightedSourceLine = signal<number | null>(null);
  readonly selectedRootCauseAttributionId = signal<string | null>(null);
  readonly activeTimelineStage = signal<ForensicTimelineStage | null>(null);

  // Connected graph elements
  readonly connectedNodeIds = signal<Set<string>>(new Set());
  readonly connectedEdgeIds = signal<Set<string>>(new Set());

  // Evidence Path (FOLLOW EVIDENCE →) state
  readonly isPathModeActive = signal<boolean>(false);
  readonly currentPathStep = signal<number>(0);
  readonly isPathPlaying = signal<boolean>(false);
  readonly playbackSpeed = signal<number>(1); // 1x or 2x
  private pathTimer: any = null;

  readonly pathSteps: ForensicPathStep[] = [
    {
      stepIndex: 0,
      stage: 'OBSERVE',
      label: 'OBSERVATION',
      nodeType: 'OBSERVATION',
      description: 'Baseline vs. candidate trajectory state capture & DOM/Network telemetry',
    },
    {
      stepIndex: 1,
      stage: 'DIFF',
      label: 'DIFFERENCE',
      nodeType: 'DIFF',
      description: 'Semantic differential extracted across DOM, network payloads, & visual render',
    },
    {
      stepIndex: 2,
      stage: 'HYPOTHESIZE',
      label: 'HYPOTHESIS',
      nodeType: 'HYPOTHESIS',
      description: 'Primary diagnostic hypothesis formulated; disproven alternatives eliminated',
    },
    {
      stepIndex: 3,
      stage: 'LOCALIZE',
      label: 'SOURCE',
      nodeType: 'SOURCE_DIFF',
      description: 'AST enclosing symbol and Git diff hunk localized with deterministic attribution',
    },
    {
      stepIndex: 4,
      stage: 'REPRODUCE',
      label: 'REPRODUCTION',
      nodeType: 'REPRODUCTION',
      description: 'Deterministic minimal replay sequence verified in isolated browser runtime',
    },
    {
      stepIndex: 5,
      stage: 'SYNTHESIZE',
      label: 'ROOT CAUSE',
      nodeType: 'ROOT_CAUSE',
      description: 'Causal root cause authoritatively identified and synthesized for regression gate',
    },
  ];

  /**
   * Primary Selection Handler for Evidence Graph Nodes.
   * Discovers topological relationships and synchronizes hypotheses, source, and root-cause.
   */
  selectEvidenceNode(
    node: EvidenceGraphNode | null,
    graph: EvidenceGraph | null,
    investigation?: InvestigationResult | null,
    explanation?: ForensicInvestigationExplanation | null
  ): void {
    if (!node) {
      this.clearSelection();
      return;
    }

    this.selectedEvidenceId.set(node.node_id);

    // Compute connected nodes and edges from DAG
    const connNodes = new Set<string>();
    const connEdges = new Set<string>();

    if (graph && graph.edges) {
      for (const edge of graph.edges) {
        if (edge.source_node_id === node.node_id) {
          connNodes.add(edge.target_node_id);
          connEdges.add(edge.edge_id);
        } else if (edge.target_node_id === node.node_id) {
          connNodes.add(edge.source_node_id);
          connEdges.add(edge.edge_id);
        }
      }
    }
    this.connectedNodeIds.set(connNodes);
    this.connectedEdgeIds.set(connEdges);

    // Synchronize matching hypothesis
    if (explanation) {
      if (
        node.node_type === 'HYPOTHESIS' ||
        explanation.primary_hypothesis.supporting_evidence_ids.some((id) => node.evidence_item_ids?.includes(id)) ||
        node.evidence_item_ids?.includes(explanation.primary_hypothesis.hypothesis_id)
      ) {
        this.highlightedHypothesisId.set(explanation.primary_hypothesis.hypothesis_id);
      } else {
        // Check eliminated hypotheses
        const matchingAlt = explanation.eliminated_alternatives.find((alt) =>
          alt.evidence_references?.some((id) => node.evidence_item_ids?.includes(id))
        );
        if (matchingAlt) {
          this.highlightedHypothesisId.set(matchingAlt.alternative_id);
        } else {
          this.highlightedHypothesisId.set(explanation.primary_hypothesis.hypothesis_id);
        }
      }
    }

    // Synchronize matching source location
    if (investigation?.root_cause?.primary_attribution?.source_location) {
      const loc = investigation.root_cause.primary_attribution.source_location;
      this.focusedSourceLocation.set({
        filePath: loc.file_path,
        startLine: loc.start_line,
        endLine: loc.end_line,
        symbolName: loc.symbol_name,
      });
      this.highlightedSourceLine.set(loc.start_line);
      this.selectedRootCauseAttributionId.set(investigation.root_cause.primary_attribution.attribution_id);
    }

    // Map node type to timeline stage
    this.mapNodeToTimelineStage(node.node_type);
  }

  hoverEvidenceNode(nodeId: string | null, graph: EvidenceGraph | null): void {
    this.hoveredEvidenceId.set(nodeId);
    if (!nodeId || !graph) {
      if (!this.selectedEvidenceId()) {
        this.connectedNodeIds.set(new Set());
        this.connectedEdgeIds.set(new Set());
      }
      return;
    }

    // When hovering without a selection, highlight direct connections
    if (!this.selectedEvidenceId()) {
      const connNodes = new Set<string>();
      const connEdges = new Set<string>();
      for (const edge of graph.edges) {
        if (edge.source_node_id === nodeId) {
          connNodes.add(edge.target_node_id);
          connEdges.add(edge.edge_id);
        } else if (edge.target_node_id === nodeId) {
          connNodes.add(edge.source_node_id);
          connEdges.add(edge.edge_id);
        }
      }
      this.connectedNodeIds.set(connNodes);
      this.connectedEdgeIds.set(connEdges);
    }
  }

  selectHypothesis(
    hypothesisId: string,
    explanation: ForensicInvestigationExplanation | null,
    graph: EvidenceGraph | null
  ): void {
    this.selectedHypothesisId.set(hypothesisId);
    this.highlightedHypothesisId.set(hypothesisId);

    if (explanation && graph) {
      // Find related evidence IDs
      let relatedEvIds: string[] = [];
      if (explanation.primary_hypothesis.hypothesis_id === hypothesisId) {
        relatedEvIds = explanation.primary_hypothesis.supporting_evidence_ids;
      } else {
        const alt = explanation.eliminated_alternatives.find((a) => a.alternative_id === hypothesisId);
        if (alt) relatedEvIds = alt.evidence_references;
      }

      // Find node in graph
      const targetNode =
        graph.nodes.find((n) => n.node_type === 'HYPOTHESIS' || n.evidence_item_ids.includes(hypothesisId)) ||
        graph.nodes.find((n) => n.evidence_item_ids.some((id) => relatedEvIds.includes(id)));
      if (targetNode) {
        this.selectEvidenceNode(targetNode, graph, null, explanation);
      }
    }
  }

  selectTimelineStage(stage: ForensicTimelineStage): void {
    this.activeTimelineStage.set(stage);
  }

  selectSourceLine(line: number, filePath?: string): void {
    this.highlightedSourceLine.set(line);
    if (filePath) {
      const current = this.focusedSourceLocation();
      if (current) {
        this.focusedSourceLocation.set({ ...current, filePath, startLine: line });
      }
    }
  }

  clearSelection(): void {
    this.selectedEvidenceId.set(null);
    this.hoveredEvidenceId.set(null);
    this.connectedNodeIds.set(new Set());
    this.connectedEdgeIds.set(new Set());
    this.highlightedHypothesisId.set(null);
    this.highlightedSourceLine.set(null);
  }

  // --- EVIDENCE PATH PLAYBACK CONTROLS ---

  startEvidencePath(graph?: EvidenceGraph | null, investigation?: InvestigationResult | null, explanation?: ForensicInvestigationExplanation | null): void {
    this.isPathModeActive.set(true);
    this.currentPathStep.set(0);
    this.applyPathStep(0, graph, investigation, explanation);
    this.playEvidencePath(graph, investigation, explanation);
  }

  playEvidencePath(graph?: EvidenceGraph | null, investigation?: InvestigationResult | null, explanation?: ForensicInvestigationExplanation | null): void {
    this.isPathPlaying.set(true);
    this.stopPathTimer();
    const intervalMs = this.playbackSpeed() === 2 ? 1500 : 2800;

    this.pathTimer = setInterval(() => {
      const next = this.currentPathStep() + 1;
      if (next < this.pathSteps.length) {
        this.setPathStep(next, graph, investigation, explanation);
      } else {
        // Complete path sequence loop or stop
        this.pauseEvidencePath();
      }
    }, intervalMs);
  }

  pauseEvidencePath(): void {
    this.isPathPlaying.set(false);
    this.stopPathTimer();
  }

  resumeEvidencePath(graph?: EvidenceGraph | null, investigation?: InvestigationResult | null, explanation?: ForensicInvestigationExplanation | null): void {
    if (this.currentPathStep() >= this.pathSteps.length - 1) {
      this.setPathStep(0, graph, investigation, explanation);
    }
    this.playEvidencePath(graph, investigation, explanation);
  }

  skipEvidencePath(graph?: EvidenceGraph | null, investigation?: InvestigationResult | null, explanation?: ForensicInvestigationExplanation | null): void {
    const next = Math.min(this.currentPathStep() + 1, this.pathSteps.length - 1);
    this.setPathStep(next, graph, investigation, explanation);
  }

  previousEvidencePathStep(graph?: EvidenceGraph | null, investigation?: InvestigationResult | null, explanation?: ForensicInvestigationExplanation | null): void {
    const prev = Math.max(this.currentPathStep() - 1, 0);
    this.setPathStep(prev, graph, investigation, explanation);
  }

  setPathStep(
    stepIndex: number,
    graph?: EvidenceGraph | null,
    investigation?: InvestigationResult | null,
    explanation?: ForensicInvestigationExplanation | null
  ): void {
    this.currentPathStep.set(stepIndex);
    this.applyPathStep(stepIndex, graph, investigation, explanation);
  }

  exitEvidencePath(): void {
    this.pauseEvidencePath();
    this.isPathModeActive.set(false);
    this.clearSelection();
  }

  togglePlaybackSpeed(): void {
    const newSpeed = this.playbackSpeed() === 1 ? 2 : 1;
    this.playbackSpeed.set(newSpeed);
    if (this.isPathPlaying()) {
      this.playEvidencePath();
    }
  }

  private applyPathStep(
    stepIndex: number,
    graph?: EvidenceGraph | null,
    investigation?: InvestigationResult | null,
    explanation?: ForensicInvestigationExplanation | null
  ): void {
    const step = this.pathSteps[stepIndex];
    if (!step) return;

    this.activeTimelineStage.set(step.stage);

    if (graph && graph.nodes) {
      const matchingNode = graph.nodes.find(
        (n) => n.node_type === step.nodeType || n.node_type.includes(step.nodeType)
      ) || graph.nodes[stepIndex % graph.nodes.length];

      if (matchingNode) {
        this.selectEvidenceNode(matchingNode, graph, investigation, explanation);
      }
    }
  }

  private mapNodeToTimelineStage(nodeType: string): void {
    switch (nodeType) {
      case 'OBSERVATION':
        this.activeTimelineStage.set('OBSERVE');
        break;
      case 'DIFF':
        this.activeTimelineStage.set('DIFF');
        break;
      case 'HYPOTHESIS':
        this.activeTimelineStage.set('HYPOTHESIZE');
        break;
      case 'SOURCE_DIFF':
        this.activeTimelineStage.set('LOCALIZE');
        break;
      case 'REPRODUCTION':
        this.activeTimelineStage.set('REPRODUCE');
        break;
      case 'ROOT_CAUSE':
        this.activeTimelineStage.set('SYNTHESIZE');
        break;
      default:
        break;
    }
  }

  private stopPathTimer(): void {
    if (this.pathTimer) {
      clearInterval(this.pathTimer);
      this.pathTimer = null;
    }
  }
}
