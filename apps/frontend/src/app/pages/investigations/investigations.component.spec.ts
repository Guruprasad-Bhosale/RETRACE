import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of } from 'rxjs';
import { InvestigationsComponent } from './investigations.component';
import { InvestigationService } from '../../core/services/investigation.service';
import { InvestigationSummaryItem } from '../../core/models/investigation.models';

describe('InvestigationsComponent', () => {
  let component: InvestigationsComponent;
  let fixture: ComponentFixture<InvestigationsComponent>;
  let service: InvestigationService;

  const mockSummaries: InvestigationSummaryItem[] = [
    {
      investigation_id: 'inv_cart_01',
      analysis_id: '11111111-2222-3333-4444-555555555555',
      regression_id: 'clf_cart_01',
      category: 'FUNCTIONAL',
      status: 'COMPLETED',
      title: 'Commerce Cart Add Disabled',
      has_generated_test: true,
      source_location: 'src/cart.ts:42-50',
      commit_hash: 'a1b2c3d4',
    },
    {
      investigation_id: 'inv_perf_02',
      analysis_id: '11111111-2222-3333-4444-555555555555',
      regression_id: 'clf_perf_02',
      category: 'PERFORMANCE',
      status: 'INCONCLUSIVE',
      title: 'Checkout Latency Spike',
      has_generated_test: false,
      source_location: null,
      commit_hash: null,
    },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InvestigationsComponent],
      providers: [
        InvestigationService,
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();

    service = TestBed.inject(InvestigationService);
    vi.spyOn(service, 'loadInvestigations').mockReturnValue(of([]));

    fixture = TestBed.createComponent(InvestigationsComponent);
    component = fixture.componentInstance;
  });

  it('should render header and metrics count', () => {
    service.investigations.set(mockSummaries);
    service.isLoading.set(false);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Investigation Command Center');
    expect(el.textContent).toContain('TOTAL INVESTIGATIONS');
    expect(component.completedCount).toBe(1);
    expect(component.inconclusiveCount).toBe(1);
  });

  it('should render investigations table rows', () => {
    service.investigations.set(mockSummaries);
    service.isLoading.set(false);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('inv_cart_01');
    expect(el.textContent).toContain('Commerce Cart Add Disabled');
    expect(el.textContent).toContain('src/cart.ts:42-50');
    expect(el.textContent).toContain('inv_perf_02');
  });

  it('should render empty state when no investigations exist', () => {
    service.investigations.set([]);
    service.isLoading.set(false);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('No matching investigations found');
  });
});
