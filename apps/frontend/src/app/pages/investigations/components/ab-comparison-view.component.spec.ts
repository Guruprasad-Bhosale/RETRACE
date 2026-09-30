import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AbComparisonViewComponent } from './ab-comparison-view.component';
import { RegressionClassification, ReproductionResult } from '../../../core/models/investigation.models';

describe('AbComparisonViewComponent', () => {
  let component: AbComparisonViewComponent;
  let fixture: ComponentFixture<AbComparisonViewComponent>;

  const mockClassification: RegressionClassification = {
    classification_id: 'clf_cart_01',
    difference_id: 'diff_cart_01',
    status: 'REGRESSION_CANDIDATE',
    category: 'FUNCTIONAL',
    rule_id: 'RULE-COMMERCE-CART-ADD-DISABLED',
    reason: 'Add to Cart button unexpectedly rendered disabled.',
    evidence: {
      difference_id: 'diff_cart_01',
      canonical_subject: 'button#add-to-cart',
      artifact_references: [],
      details: {
        text_a: 'Add to Cart',
        text_b: 'Out of Stock',
        stock_a: 10,
        stock_b: 0,
      },
    },
    created_at: '2026-09-30T10:00:00Z',
  };

  const mockReproduction: ReproductionResult = {
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
      matched_evidence: ['disabled'],
      mismatched_evidence: [],
      notes: 'Disabled attribute matches regression signature',
    },
    total_duration_ms: 1000,
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AbComparisonViewComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(AbComparisonViewComponent);
    component = fixture.componentInstance;
  });

  it('should render baseline vs regressed comparison cards', () => {
    fixture.componentRef.setInput('classification', mockClassification);
    fixture.componentRef.setInput('reproduction', mockReproduction);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Version A (Baseline)');
    expect(el.textContent).toContain('Version B (Candidate)');
    expect(el.textContent).toContain('EXPECTED');
    expect(el.textContent).toContain('REGRESSION');
    expect(el.textContent).toContain('Add to Cart');
    expect(el.textContent).toContain('Out of Stock');
  });

  it('should render structured diff entries', () => {
    fixture.componentRef.setInput('classification', mockClassification);
    fixture.componentRef.setInput('reproduction', mockReproduction);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('stock');
    expect(el.textContent).toContain('10');
    expect(el.textContent).toContain('0');
  });
});
