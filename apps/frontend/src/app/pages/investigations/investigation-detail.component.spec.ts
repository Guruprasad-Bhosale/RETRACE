import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of } from 'rxjs';
import { InvestigationDetailComponent } from './investigation-detail.component';
import { InvestigationService } from '../../core/services/investigation.service';
import { InvestigationResult } from '../../core/models/investigation.models';

describe('InvestigationDetailComponent', () => {
  let component: InvestigationDetailComponent;
  let fixture: ComponentFixture<InvestigationDetailComponent>;
  let service: InvestigationService;

  const mockInvestigation: InvestigationResult = {
    investigation_id: 'inv_cart_01',
    analysis_id: '11111111-2222-3333-4444-555555555555',
    regression_id: 'clf_cart_01',
    status: 'COMPLETED',
    created_at: '2026-09-30T10:00:00Z',
    classification: {
      classification_id: 'clf_cart_01',
      difference_id: 'diff_cart_01',
      status: 'REGRESSION_CANDIDATE',
      category: 'FUNCTIONAL',
      rule_id: 'RULE-COMMERCE-CART-ADD-DISABLED',
      reason: 'Add to Cart button disabled',
      evidence: {
        difference_id: 'diff_cart_01',
        canonical_subject: 'button#add-to-cart',
        artifact_references: [],
        details: {},
      },
      created_at: '2026-09-30T10:00:00Z',
    },
    reproduction: {
      reproduction_id: 'repro_cart_01',
      classification_id: 'clf_cart_01',
      difference_id: 'diff_cart_01',
      rule_id: 'RULE-COMMERCE-CART-ADD-DISABLED',
      category: 'FUNCTIONAL',
      status: 'REPRODUCED',
      strategy: 'DIRECT_REPLAY',
      path: {
        path_id: 'path_01',
        trajectory_id: 'traj_01',
        classification_id: 'clf_cart_01',
        difference_id: 'diff_cart_01',
        seed_url: 'https://store.example.com',
        steps: [],
        path_signature: 'sig_01',
        observation_ids: [],
      },
      attempts: [],
      final_verification: {
        expected_difference_id: 'diff_cart_01',
        expected_classification_id: 'clf_cart_01',
        expected_rule_id: 'RULE-COMMERCE-CART-ADD-DISABLED',
        expected_category: 'FUNCTIONAL',
        match_status: 'FULL_MATCH',
        observed_match: true,
        matched_evidence: [],
        mismatched_evidence: [],
        notes: 'Match confirmed',
      },
      total_duration_ms: 1200,
    },
    root_cause: {
      root_cause_id: 'rc_cart_01',
      classification_id: 'clf_cart_01',
      difference_id: 'diff_cart_01',
      category: 'FUNCTIONAL',
      status: 'LOCATED',
      attributions: [],
      primary_attribution: null,
      candidate_locations: [],
    },
    generated_test: {
      test_id: 'test_cart_01',
      regression_id: 'clf_cart_01',
      framework: 'PLAYWRIGHT',
      language: 'TYPESCRIPT',
      target_version: 'v2',
      title: 'Cart Regression Test',
      description: 'Test description',
      status: 'SYNTHESIZED',
      validation_status: 'STRUCTURALLY_VALIDATED',
      generated_source: '// test code',
      steps: [],
      assertions: [],
      provenance: {
        classification_id: 'clf_cart_01',
        difference_id: 'diff_cart_01',
        source_locations: [],
        commit_hashes: [],
      },
      validation_notes: [],
    },
    report: {
      report_id: 'rep_cart_01',
      regression_id: 'clf_cart_01',
      title: 'Cart Regression Report',
      status: 'COMPLETE',
      summary: 'Executive summary for cart test',
      markdown_content: '# Cart Report',
      json_content: {},
      sections: [],
      evidence_chain: {
        chain_id: 'chain_01',
        nodes: [],
      },
    },
    artifacts: [],
    provenance: {
      analysis_id: '11111111-2222-3333-4444-555555555555',
      classification_id: 'clf_cart_01',
      difference_id: 'diff_cart_01',
      artifact_references: [],
    },
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InvestigationDetailComponent],
      providers: [
        InvestigationService,
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: of({
              get: (key: string) => (key === 'id' ? 'inv_cart_01' : null),
            }),
          },
        },
      ],
    }).compileComponents();

    service = TestBed.inject(InvestigationService);
    vi.spyOn(service, 'loadInvestigationById').mockReturnValue(of(null));

    fixture = TestBed.createComponent(InvestigationDetailComponent);
    component = fixture.componentInstance;
  });

  it('should render investigation header details and tabs', () => {
    service.selectedInvestigation.set(mockInvestigation);
    component.investigationId.set('inv_cart_01');
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('inv_cart_01');
    expect(el.textContent).toContain('FUNCTIONAL');
    expect(el.textContent).toContain('Overview');
    expect(el.textContent).toContain('Reproduction');
    expect(el.textContent).toContain('Source & Root Cause');
    expect(el.textContent).toContain('Playwright Test');
    expect(el.textContent).toContain('Evidence Report');
  });

  it('should switch tabs when clicked', () => {
    service.selectedInvestigation.set(mockInvestigation);
    fixture.detectChanges();

    component.activeTab.set('reproduction');
    expect(component.activeTab()).toBe('reproduction');

    component.activeTab.set('source-diff');
    expect(component.activeTab()).toBe('source-diff');
  });

  it('should render error state when error is present', () => {
    service.selectedInvestigation.set(null);
    service.error.set('Investigation not found');
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Unable to load investigation');
    expect(el.textContent).toContain('Investigation not found');
  });
});
