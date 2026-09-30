import { ComponentFixture, TestBed } from '@angular/core/testing';
import { StatusBadgeComponent } from './status-badge.component';

describe('StatusBadgeComponent', () => {
  let component: StatusBadgeComponent;
  let fixture: ComponentFixture<StatusBadgeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StatusBadgeComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(StatusBadgeComponent);
    component = fixture.componentInstance;
  });

  it('should render LOCATED status with emerald badge', () => {
    fixture.componentRef.setInput('status', 'LOCATED');
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('LOCATED');
    expect(el.firstElementChild?.className).toContain('text-emerald-300');
  });

  it('should render INCONCLUSIVE status with purple badge', () => {
    fixture.componentRef.setInput('status', 'INCONCLUSIVE');
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('INCONCLUSIVE');
    expect(el.firstElementChild?.className).toContain('text-purple-300');
  });

  it('should render CANDIDATE_ONLY status with amber badge', () => {
    fixture.componentRef.setInput('status', 'CANDIDATE_ONLY');
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('CANDIDATE_ONLY');
    expect(el.firstElementChild?.className).toContain('text-amber-300');
  });

  it('should render FAILED status with rose badge', () => {
    fixture.componentRef.setInput('status', 'FAILED');
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('FAILED');
    expect(el.firstElementChild?.className).toContain('text-rose-300');
  });
});
