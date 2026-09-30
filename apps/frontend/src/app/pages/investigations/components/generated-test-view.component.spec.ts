import { ComponentFixture, TestBed } from '@angular/core/testing';
import { GeneratedTestViewComponent } from './generated-test-view.component';
import { GeneratedTest } from '../../../core/models/investigation.models';

describe('GeneratedTestViewComponent', () => {
  let component: GeneratedTestViewComponent;
  let fixture: ComponentFixture<GeneratedTestViewComponent>;

  const mockTest: GeneratedTest = {
    test_id: 'test_cart_01',
    regression_id: 'clf_cart_01',
    reproduction_id: 'repro_cart_01',
    root_cause_id: 'rc_cart_01',
    framework: 'PLAYWRIGHT',
    language: 'TYPESCRIPT',
    target_version: 'v2',
    title: 'Commerce Cart Regression Test',
    description: 'Playwright test verifying Add to Cart disabled regression.',
    status: 'SYNTHESIZED',
    validation_status: 'STRUCTURALLY_VALIDATED',
    generated_source: "import { test, expect } from '@playwright/test';\n\ntest('regression: add to cart', async ({ page }) => {\n  await page.goto('/products/1');\n  await expect(page.locator('#add-to-cart')).toBeEnabled();\n});",
    steps: [],
    assertions: [],
    provenance: {
      classification_id: 'clf_cart_01',
      difference_id: 'diff_cart_01',
      reproduction_id: 'repro_cart_01',
      root_cause_id: 'rc_cart_01',
      source_locations: ['apps/commerce/src/cart.ts:42-48'],
      commit_hashes: ['a1b2c3d4'],
    },
    validation_notes: [],
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GeneratedTestViewComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(GeneratedTestViewComponent);
    component = fixture.componentInstance;
  });

  it('should render generated test source code and metadata', () => {
    fixture.componentRef.setInput('generatedTest', mockTest);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('PLAYWRIGHT');
    expect(el.textContent).toContain('TYPESCRIPT');
    expect(el.textContent).toContain('STRUCTURALLY_VALIDATED');
    expect(el.textContent).toContain("test('regression: add to cart'");
  });

  it('should clearly indicate DERIVED TEST ARTIFACT disclaimer', () => {
    fixture.componentRef.setInput('generatedTest', mockTest);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('DERIVED TEST ARTIFACT');
  });

  it('should render empty state when test is null', () => {
    fixture.componentRef.setInput('generatedTest', null);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Test source code not available');
  });
});
