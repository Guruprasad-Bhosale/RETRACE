import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach } from 'vitest';
import { HypothesesViewComponent } from './hypotheses-view.component';
import { ForensicInvestigationExplanation } from '../../../core/models/investigation.models';

describe('HypothesesViewComponent', () => {
  let component: HypothesesViewComponent;
  let fixture: ComponentFixture<HypothesesViewComponent>;

  const sampleExplanation: ForensicInvestigationExplanation = {
    investigation_id: 'inv_01',
    root_cause_summary: 'Subtotal calculation modified',
    root_cause_status: 'CONFIRMED',
    primary_hypothesis: {
      hypothesis_id: 'hyp_01',
      title: 'Calculation logic altered in cart handler',
      description: 'Discount logic altered in pricing component',
      category: 'CALCULATION_LOGIC',
      status: 'CONFIRMED',
      supporting_evidence_ids: ['ev_1'],
      contradicting_evidence_ids: [],
      score: 0.95,
    },
    eliminated_alternatives: [
      {
        alternative_id: 'alt_01',
        title: 'Client-side CSS formatting',
        category: 'STYLING_FORMATTING',
        status: 'ELIMINATED',
        elimination_reason: 'CSS unchanged; arithmetic mismatch reproduced.',
        evidence_references: ['ev_1'],
      },
    ],
    evidence_graph: {
      graph_id: 'g1',
      investigation_id: 'inv_01',
      nodes: [],
      edges: [],
      deterministic_hash: 'hash',
      created_at: '2026-10-03T10:00:00Z',
    },
    confidence: {
      level: 'HIGH',
      score: 0.95,
      supporting_count: 2,
      contradicting_count: 0,
      unresolved_count: 0,
      rationale: 'High confidence with deterministic reproduction.',
    },
    falsification: {
      condition_id: 'fals_01',
      statement: 'If Version B reproduces without the patch, conclusion is false.',
      testable_verification: 'Revert patch and re-run.',
      potential_confounders: ['Caching'],
    },
    provenance_chain: ['Obs', 'Diff', 'RootCause'],
    evidence_graph_available: true,
    created_at: '2026-10-03T10:00:00Z',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HypothesesViewComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(HypothesesViewComponent);
    component = fixture.componentInstance;
    component.explanation = sampleExplanation;
    fixture.detectChanges();
  });

  it('should render primary hypothesis and eliminated alternatives', () => {
    expect(component).toBeTruthy();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Calculation logic altered in cart handler');
    expect(compiled.textContent).toContain('Client-side CSS formatting');
    expect(compiled.textContent).toContain('CSS unchanged; arithmetic mismatch reproduced.');
  });

  it('should handle hypothesis selection and synchronize state', () => {
    component.onHypothesisClick('hyp_01');
    expect(component.forensic.selectedHypothesisId()).toBe('hyp_01');
    expect(component.forensic.highlightedHypothesisId()).toBe('hyp_01');
  });

  it('should return appropriate state badge classes for hypothesis states', () => {
    expect(component.getHypothesisStateBadgeClass('CONFIRMED')).toContain('emerald');
    expect(component.getHypothesisStateBadgeClass('ELIMINATED')).toContain('red');
    expect(component.getHypothesisStateBadgeClass('PROPOSED')).toContain('amber');
  });
});
