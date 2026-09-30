import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReproductionTimelineComponent } from './reproduction-timeline.component';
import { ReproductionResult } from '../../../core/models/investigation.models';

describe('ReproductionTimelineComponent', () => {
  let component: ReproductionTimelineComponent;
  let fixture: ComponentFixture<ReproductionTimelineComponent>;

  const mockRepro: ReproductionResult = {
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
      steps: [
        {
          step_index: 0,
          action_type: 'NAVIGATE',
          raw_target: 'https://store.example.com/products/1',
          target_strategy: 'URL',
          timeout_ms: 5000,
        },
        {
          step_index: 1,
          action_type: 'CLICK',
          raw_target: '#add-to-cart',
          target_strategy: 'CSS_SELECTOR',
          timeout_ms: 3000,
        },
      ],
      path_signature: 'sig_01',
      observation_ids: ['obs_01', 'obs_02'],
    },
    attempts: [],
    final_verification: {
      expected_difference_id: 'diff_cart_01',
      expected_classification_id: 'clf_cart_01',
      expected_rule_id: 'RULE-COMMERCE-CART-ADD-DISABLED',
      expected_category: 'FUNCTIONAL',
      match_status: 'FULL_MATCH',
      observed_match: true,
      matched_evidence: ['text', 'disabled'],
      mismatched_evidence: [],
      notes: 'Observed disabled state matches regression signature',
    },
    total_duration_ms: 2500,
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReproductionTimelineComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ReproductionTimelineComponent);
    component = fixture.componentInstance;
  });

  it('should render reproduction details and steps', () => {
    fixture.componentRef.setInput('reproduction', mockRepro);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('DIRECT_REPLAY');
    expect(el.textContent).toContain('FULL_MATCH');
    expect(el.textContent).toContain('NAVIGATE');
    expect(el.textContent).toContain('CLICK');
    expect(el.textContent).toContain('#add-to-cart');
  });

  it('should render empty state when reproduction is null', () => {
    fixture.componentRef.setInput('reproduction', null);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('No causal reproduction action steps available');
  });
});
