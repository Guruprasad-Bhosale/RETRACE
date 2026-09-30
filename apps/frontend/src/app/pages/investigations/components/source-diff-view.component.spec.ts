import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SourceDiffViewComponent } from './source-diff-view.component';
import { RootCauseResult } from '../../../core/models/investigation.models';

describe('SourceDiffViewComponent', () => {
  let component: SourceDiffViewComponent;
  let fixture: ComponentFixture<SourceDiffViewComponent>;

  const mockRootCause: RootCauseResult = {
    root_cause_id: 'rc_cart_01',
    classification_id: 'clf_cart_01',
    difference_id: 'diff_cart_01',
    category: 'FUNCTIONAL',
    status: 'LOCATED',
    attributions: [
      {
        attribution_id: 'attr_01',
        source_location: {
          repository_path: 'apps/commerce',
          file_path: 'apps/commerce/src/cart.ts',
          symbol_name: 'canAddToCart',
          start_line: 42,
          start_column: 1,
          end_line: 48,
          end_column: 2,
        },
        relationship_type: 'DIRECTLY_CHANGED',
        commit_attribution_type: 'INTRODUCING_COMMIT',
        explanation: 'Direct modification to threshold check condition',
        commit: {
          commit_hash: 'a1b2c3d4e5f6',
          author_name: 'Alice Engineer',
          author_email: 'alice@example.com',
          timestamp: '2026-09-30T10:00:00Z',
          message: 'Refactor inventory check logic',
          parent_hashes: [],
          is_merge: false,
        },
        diff_hunk: {
          old_start: 42,
          old_lines: 6,
          new_start: 42,
          new_lines: 8,
          header: '@@ -42,6 +42,8 @@ function canAddToCart',
          added_lines: [43],
          deleted_lines: [43],
          lines: [
            { change_type: 'CONTEXT', content: 'function canAddToCart(item: Item): boolean {', old_line_number: 42, new_line_number: 42 },
            { change_type: 'DELETION', content: '-  return item.stock > 0;', old_line_number: 43, new_line_number: null },
            { change_type: 'ADDITION', content: '+  return item.stock > 10; // regression: threshold raised', old_line_number: null, new_line_number: 43 },
            { change_type: 'CONTEXT', content: '}', old_line_number: 44, new_line_number: 44 },
          ],
        },
      },
    ],
    primary_attribution: null,
    candidate_locations: [],
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SourceDiffViewComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(SourceDiffViewComponent);
    component = fixture.componentInstance;
  });

  it('should render source attribution location and symbol', () => {
    fixture.componentRef.setInput('rootCause', mockRootCause);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('apps/commerce/src/cart.ts');
    expect(el.textContent).toContain('canAddToCart');
    expect(el.textContent).toContain('DIRECTLY_CHANGED');
    expect(el.textContent).toContain('INTRODUCING_COMMIT');
    expect(el.textContent).toContain('a1b2c3d4');
  });

  it('should render diff lines with addition and deletion', () => {
    fixture.componentRef.setInput('rootCause', mockRootCause);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('return item.stock > 0;');
    expect(el.textContent).toContain('return item.stock > 10;');
  });

  it('should handle INCONCLUSIVE root cause gracefully', () => {
    const inconclusiveRC: RootCauseResult = {
      root_cause_id: 'rc_inconclusive',
      classification_id: 'clf_02',
      difference_id: 'diff_02',
      category: 'PERFORMANCE',
      status: 'INCONCLUSIVE',
      attributions: [],
      primary_attribution: null,
      candidate_locations: [],
    };
    fixture.componentRef.setInput('rootCause', inconclusiveRC);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('INCONCLUSIVE');
    expect(el.textContent).toContain('Inconclusive Attribution');
  });
});
