import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach } from 'vitest';
import { EvidenceGraphViewComponent } from './evidence-graph-view.component';
import { EvidenceGraph } from '../../../core/models/investigation.models';

describe('EvidenceGraphViewComponent', () => {
  let component: EvidenceGraphViewComponent;
  let fixture: ComponentFixture<EvidenceGraphViewComponent>;

  const sampleGraph: EvidenceGraph = {
    graph_id: 'graph_test_01',
    investigation_id: 'inv_01',
    nodes: [
      {
        node_id: 'n1',
        node_type: 'OBSERVATION',
        title: 'Browser Observation',
        status: 'VERIFIED',
        evidence_item_ids: ['ev_1'],
        confidence_score: 1.0,
      },
      {
        node_id: 'n2',
        node_type: 'DIFF',
        title: 'Price Total Discrepancy',
        status: 'CONFIRMED',
        evidence_item_ids: ['ev_2'],
        confidence_score: 0.95,
      },
    ],
    edges: [
      {
        edge_id: 'e1',
        source_node_id: 'n1',
        target_node_id: 'n2',
        relationship: 'DERIVED_FROM',
        weight: 1.0,
        explanation: 'Derived from observation',
      },
    ],
    deterministic_hash: 'abc123hash',
    created_at: '2026-10-03T10:00:00Z',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EvidenceGraphViewComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(EvidenceGraphViewComponent);
    component = fixture.componentInstance;
    component.graph = sampleGraph;
    fixture.detectChanges();
  });

  it('should create and render node cards', () => {
    expect(component).toBeTruthy();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Browser Observation');
    expect(compiled.textContent).toContain('Price Total Discrepancy');
  });

  it('should select and toggle node upon click', () => {
    component.onNodeClick(sampleGraph.nodes[0]);
    fixture.detectChanges();
    expect(component.forensic.selectedEvidenceId()).toBe('n1');
    expect(component.selectedNodeDetails?.node_id).toBe('n1');

    // Deselect
    component.onNodeClick(sampleGraph.nodes[0]);
    fixture.detectChanges();
    expect(component.forensic.selectedEvidenceId()).toBeNull();
  });

  it('should support arrow key navigation across nodes', () => {
    component.handleKeyDown(new KeyboardEvent('keydown', { key: 'ArrowRight' }));
    expect(component.forensic.selectedEvidenceId()).toBe('n1');

    component.handleKeyDown(new KeyboardEvent('keydown', { key: 'ArrowRight' }));
    expect(component.forensic.selectedEvidenceId()).toBe('n2');

    component.handleKeyDown(new KeyboardEvent('keydown', { key: 'Escape' }));
    expect(component.forensic.selectedEvidenceId()).toBeNull();
  });

  it('should start Follow Evidence playback', () => {
    component.startFollowEvidence();
    expect(component.forensic.isPathModeActive()).toBe(true);
    expect(component.forensic.currentPathStep()).toBe(0);
    component.forensic.exitEvidencePath();
  });
});
