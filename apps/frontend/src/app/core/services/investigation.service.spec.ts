import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { InvestigationService } from './investigation.service';
import { InvestigationSummaryItem } from '../models/investigation.models';

describe('InvestigationService', () => {
  let service: InvestigationService;
  let httpMock: HttpTestingController;

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

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        InvestigationService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(InvestigationService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
    expect(service.investigations().length).toBe(0);
    expect(service.isLoading()).toBe(false);
  });

  it('should load investigations and update signals', () => {
    service.loadInvestigations().subscribe((items) => {
      expect(items.length).toBe(2);
      expect(service.investigations().length).toBe(2);
      expect(service.isLoading()).toBe(false);
    });

    const req = httpMock.expectOne('http://localhost:8000/api/v1/investigations');
    expect(req.request.method).toBe('GET');
    req.flush(mockSummaries);
  });

  it('should filter investigations by status correctly', () => {
    service.investigations.set(mockSummaries);

    service.setStatusFilter('COMPLETED');
    expect(service.filteredInvestigations().length).toBe(1);
    expect(service.filteredInvestigations()[0].investigation_id).toBe('inv_cart_01');

    service.setStatusFilter('INCONCLUSIVE');
    expect(service.filteredInvestigations().length).toBe(1);
    expect(service.filteredInvestigations()[0].investigation_id).toBe('inv_perf_02');

    service.setStatusFilter('ALL');
    expect(service.filteredInvestigations().length).toBe(2);
  });

  it('should filter investigations by category correctly', () => {
    service.investigations.set(mockSummaries);

    service.setCategoryFilter('FUNCTIONAL');
    expect(service.filteredInvestigations().length).toBe(1);
    expect(service.filteredInvestigations()[0].category).toBe('FUNCTIONAL');

    service.setCategoryFilter('PERFORMANCE');
    expect(service.filteredInvestigations().length).toBe(1);

    service.setCategoryFilter('ALL');
    expect(service.filteredInvestigations().length).toBe(2);
  });

  it('should search investigations by keyword', () => {
    service.investigations.set(mockSummaries);

    service.setSearchQuery('cart');
    expect(service.filteredInvestigations().length).toBe(1);
    expect(service.filteredInvestigations()[0].investigation_id).toBe('inv_cart_01');

    service.setSearchQuery('Latency');
    expect(service.filteredInvestigations().length).toBe(1);
    expect(service.filteredInvestigations()[0].investigation_id).toBe('inv_perf_02');

    service.setSearchQuery('nonexistent');
    expect(service.filteredInvestigations().length).toBe(0);
  });

  it('should handle error when loading investigations', () => {
    service.loadInvestigations().subscribe((items) => {
      expect(items.length).toBe(0);
      expect(service.error()).toBeTruthy();
      expect(service.isLoading()).toBe(false);
    });

    const req = httpMock.expectOne('http://localhost:8000/api/v1/investigations');
    req.error(new ProgressEvent('Network error'), { status: 500, statusText: 'Server Error' });
  });

  it('should handle 503 Service Unavailable and update error signal gracefully', () => {
    service.loadInvestigations().subscribe((items) => {
      expect(items.length).toBe(0);
      expect(service.error()).toContain('503');
      expect(service.isLoading()).toBe(false);
    });

    const req = httpMock.expectOne('http://localhost:8000/api/v1/investigations');
    req.flush({ detail: 'Service Unavailable: database pool exhausted' }, { status: 503, statusText: 'Service Unavailable' });
  });

  it('should handle 404 Not Found when loading investigation detail', () => {
    service.loadInvestigationById('nonexistent_id').subscribe((result) => {
      expect(result).toBeNull();
      expect(service.error()).toBeTruthy();
      expect(service.selectedInvestigation()).toBeNull();
      expect(service.isLoading()).toBe(false);
    });

    const req = httpMock.expectOne('http://localhost:8000/api/v1/investigations/nonexistent_id');
    req.flush({ detail: 'Investigation not found' }, { status: 404, statusText: 'Not Found' });
  });
});
