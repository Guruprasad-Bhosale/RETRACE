import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { InvestigationReplayComparisonComponent } from './investigation-replay-comparison.component';
import { InvestigationService } from '../../../core/services/investigation.service';
import { ReplayResult, InvestigationComparisonResult } from '../../../core/models/investigation.models';

describe('InvestigationReplayComparisonComponent', () => {
  let component: InvestigationReplayComparisonComponent;
  let fixture: ComponentFixture<InvestigationReplayComparisonComponent>;
  let mockInvestigationService: any;


  const mockReplayResult: ReplayResult = {
    replay_id: 'rep_123456',
    investigation_id: 'inv_test_01',
    snapshot_hash: 'abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
    analysis_version: 'forensics-v1',
    graph_hash: '1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
    hypothesis_hash: 'fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321',
    explanation_hash: '9876543210abcdef9876543210abcdef9876543210abcdef9876543210abcdef',
    status: 'REPRODUCIBLE',
    is_reproducible: true,
    divergence_details: [],
    created_at: new Date().toISOString(),
  };

  const mockComparisonResult: InvestigationComparisonResult = {
    investigation_a_id: 'inv_test_01',
    investigation_b_id: 'inv_test_02',
    shared_evidence_count: 5,
    unique_evidence_a_count: 1,
    unique_evidence_b_count: 2,
    root_cause_matches: true,
    hypothesis_matches: true,
    graph_diff: [],
    explanation_diff: [],
    created_at: new Date().toISOString(),
  };

  beforeEach(async () => {
    mockInvestigationService = {
      loadInvestigations: () => of([]),
      replayInvestigation: () => of(mockReplayResult),
      compareInvestigations: () => of(mockComparisonResult),
    };

    await TestBed.configureTestingModule({
      imports: [InvestigationReplayComparisonComponent],
      providers: [{ provide: InvestigationService, useValue: mockInvestigationService }],
    }).compileComponents();

    fixture = TestBed.createComponent(InvestigationReplayComparisonComponent);
    component = fixture.componentInstance;
    component.investigationId = 'inv_test_01';
    fixture.detectChanges();
  });

  it('should create and initialize replay comparison component', () => {
    expect(component).toBeTruthy();
  });

  it('should execute triggerReplay and update replayResult signal', () => {
    component.triggerReplay();
    expect(component.replayResult()?.status).toBe('REPRODUCIBLE');
    expect(component.replayResult()?.is_reproducible).toBe(true);
  });

  it('should execute triggerComparison and update comparisonResult signal', () => {
    component.selectedOtherId = 'inv_test_02';
    component.triggerComparison();
    expect(component.comparisonResult()?.shared_evidence_count).toBe(5);
    expect(component.comparisonResult()?.root_cause_matches).toBe(true);
  });
});
