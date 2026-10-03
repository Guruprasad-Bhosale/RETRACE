import { TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach } from 'vitest';
import { ForensicInteractionService } from './forensic-interaction.service';
import {
  EvidenceGraph,
  ForensicInvestigationExplanation,
  InvestigationResult,
} from '../models/investigation.models';

describe('ForensicInteractionService', () => {
  let service: ForensicInteractionService;

  const mockGraph: EvidenceGraph = {
    graph_id: 'graph-1',
    investigation_id: 'inv-1',
    deterministic_hash: 'hash-abc',
    created_at: '2026-10-03T10:00:00Z',
    nodes: [
      {
        node_id: 'node-obs-1',
        node_type: 'OBSERVATION',
        title: 'POST /checkout failed',
        status: 'CONFIRMED',
        evidence_item_ids: ['ev-1'],
        confidence_score: 0.98,
      },
      {
        node_id: 'node-hyp-1',
        node_type: 'HYPOTHESIS',
        title: 'Checkout handler disables button',
        status: 'CONFIRMED',
        evidence_item_ids: ['ev-1', 'hyp-1'],
        confidence_score: 0.95,
      },
      {
        node_id: 'node-src-1',
        node_type: 'SOURCE_DIFF',
        title: 'checkout.ts line 142 mutation',
        status: 'CONFIRMED',
        evidence_item_ids: ['ev-2'],
        confidence_score: 0.92,
      },
    ],
    edges: [
      {
        edge_id: 'edge-1',
        source_node_id: 'node-obs-1',
        target_node_id: 'node-hyp-1',
        relationship: 'SUPPORTS',
        weight: 1.0,
        explanation: 'Observation provides empirical grounding for checkout hypothesis',
      },
      {
        edge_id: 'edge-2',
        source_node_id: 'node-hyp-1',
        target_node_id: 'node-src-1',
        relationship: 'CAUSED_BY',
        weight: 0.9,
        explanation: 'Hypothesis is directly localized to source diff',
      },
    ],
  };

  const mockExplanation: ForensicInvestigationExplanation = {
    investigation_id: 'inv-1',
    root_cause_summary: 'Disabled button prevented checkout dispatch',
    root_cause_status: 'LOCATED',
    evidence_graph_available: true,
    created_at: '2026-10-03T10:00:00Z',
    evidence_graph: mockGraph,
    provenance_chain: ['obs-1', 'hyp-1'],
    primary_hypothesis: {
      hypothesis_id: 'hyp-1',
      title: 'Checkout handler disables button',
      description: 'Button state prevents network payload delivery',
      category: 'DOM_RENDER_LOGIC',
      status: 'CONFIRMED',
      supporting_evidence_ids: ['ev-1'],
      contradicting_evidence_ids: [],
      score: 0.95,
    },
    eliminated_alternatives: [
      {
        alternative_id: 'alt-1',
        title: 'API Gateway timeout',
        category: 'API_CONTRACT',
        status: 'ELIMINATED',
        elimination_reason: 'Network traces show request never reached proxy',
        evidence_references: ['ev-99'],
      },
    ],
    confidence: {
      level: 'HIGH',
      score: 0.95,
      supporting_count: 2,
      contradicting_count: 0,
      unresolved_count: 0,
      rationale: 'Multiple empirical layers confirm root cause',
    },
    falsification: {
      condition_id: 'fals-1',
      statement: 'If button remains enabled, POST /checkout must fire',
      testable_verification: 'Re-enable submit element in headless browser',
      potential_confounders: ['Adblocker extension'],
    },
  };

  const mockInvestigation: Partial<InvestigationResult> = {
    investigation_id: 'inv-1',
    status: 'COMPLETED',
    root_cause: {
      root_cause_id: 'rc-1',
      classification_id: 'cls-1',
      difference_id: 'diff-1',
      category: 'DOM_RENDER_LOGIC',
      status: 'LOCATED',
      attributions: [],
      candidate_locations: [],
      primary_attribution: {
        attribution_id: 'attr-1',
        relationship_type: 'DIRECTLY_CHANGED',
        commit_attribution_type: 'CAUSAL_COMMIT',
        explanation: 'Button disabled prop was added unconditionally',
        source_location: {
          repository_path: 'app/checkout.ts',
          file_path: 'src/checkout.ts',
          start_line: 142,
          end_line: 145,
          start_column: 1,
          end_column: 20,
          symbol_name: 'onCheckoutSubmit',
        },
      },
    },
  };

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ForensicInteractionService);
  });

  it('should initialize with default empty selection state', () => {
    expect(service.selectedEvidenceId()).toBeNull();
    expect(service.hoveredEvidenceId()).toBeNull();
    expect(service.connectedNodeIds().size).toBe(0);
    expect(service.connectedEdgeIds().size).toBe(0);
    expect(service.isPathModeActive()).toBe(false);
  });

  it('should compute connected nodes and edges when selecting evidence node', () => {
    const targetNode = mockGraph.nodes[0]; // node-obs-1
    service.selectEvidenceNode(targetNode, mockGraph, mockInvestigation as any, mockExplanation);

    expect(service.selectedEvidenceId()).toBe('node-obs-1');
    expect(service.connectedNodeIds().has('node-hyp-1')).toBe(true);
    expect(service.connectedEdgeIds().has('edge-1')).toBe(true);
    expect(service.activeTimelineStage()).toBe('OBSERVE');
  });

  it('should synchronize matching hypothesis when selecting node', () => {
    const targetNode = mockGraph.nodes[1]; // node-hyp-1
    service.selectEvidenceNode(targetNode, mockGraph, mockInvestigation as any, mockExplanation);

    expect(service.highlightedHypothesisId()).toBe('hyp-1');
    expect(service.activeTimelineStage()).toBe('HYPOTHESIZE');
  });

  it('should synchronize source location and line when root cause is available', () => {
    const targetNode = mockGraph.nodes[2]; // node-src-1
    service.selectEvidenceNode(targetNode, mockGraph, mockInvestigation as any, mockExplanation);

    expect(service.focusedSourceLocation()?.filePath).toBe('src/checkout.ts');
    expect(service.focusedSourceLocation()?.startLine).toBe(142);
    expect(service.highlightedSourceLine()).toBe(142);
  });

  it('should handle hypothesis selection and activate matching graph node', () => {
    service.selectHypothesis('hyp-1', mockExplanation, mockGraph);

    expect(service.selectedHypothesisId()).toBe('hyp-1');
    expect(service.highlightedHypothesisId()).toBe('hyp-1');
    expect(service.selectedEvidenceId()).toBe('node-hyp-1');
  });

  it('should control evidence path sequential playback', () => {
    service.startEvidencePath(mockGraph, mockInvestigation as any, mockExplanation);

    expect(service.isPathModeActive()).toBe(true);
    expect(service.currentPathStep()).toBe(0);

    service.skipEvidencePath(mockGraph, mockInvestigation as any, mockExplanation);
    expect(service.currentPathStep()).toBe(1);

    service.pauseEvidencePath();
    expect(service.isPathPlaying()).toBe(false);

    service.togglePlaybackSpeed();
    expect(service.playbackSpeed()).toBe(2);

    service.exitEvidencePath();
    expect(service.isPathModeActive()).toBe(false);
    expect(service.selectedEvidenceId()).toBeNull();
  });
});
