import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, catchError, of, tap } from 'rxjs';
import {
  InvestigationResult,
  InvestigationSummaryItem,
} from '../models/investigation.models';

@Injectable({
  providedIn: 'root',
})
export class InvestigationService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000/api/v1';

  // Signals for state management
  readonly investigations = signal<InvestigationSummaryItem[]>([]);
  readonly selectedInvestigation = signal<InvestigationResult | null>(null);
  readonly selectedTab = signal<string>('overview');
  readonly isLoading = signal<boolean>(false);
  readonly error = signal<string | null>(null);

  // Filters
  readonly statusFilter = signal<string>('ALL');
  readonly categoryFilter = signal<string>('ALL');
  readonly searchQuery = signal<string>('');

  // Computed filtered investigations
  readonly filteredInvestigations = computed(() => {
    const list = this.investigations();
    const status = this.statusFilter();
    const category = this.categoryFilter();
    const query = this.searchQuery().trim().toLowerCase();

    return list.filter((item) => {
      // Status filter
      if (status !== 'ALL' && item.status !== status) {
        return false;
      }
      // Category filter
      if (category !== 'ALL' && item.category !== category) {
        return false;
      }
      // Search query
      if (query) {
        const matchId = item.investigation_id.toLowerCase().includes(query);
        const matchTitle = item.title.toLowerCase().includes(query);
        const matchCategory = item.category.toLowerCase().includes(query);
        const matchLocation = item.source_location ? item.source_location.toLowerCase().includes(query) : false;
        const matchCommit = item.commit_hash ? item.commit_hash.toLowerCase().includes(query) : false;
        if (!matchId && !matchTitle && !matchCategory && !matchLocation && !matchCommit) {
          return false;
        }
      }
      return true;
    });
  });

  loadInvestigations(analysisId?: string): Observable<InvestigationSummaryItem[]> {
    this.isLoading.set(true);
    this.error.set(null);

    let params = new HttpParams();
    if (analysisId) {
      params = params.set('analysis_id', analysisId);
    }

    return this.http.get<InvestigationSummaryItem[]>(`${this.baseUrl}/investigations`, { params }).pipe(
      tap((items) => {
        this.investigations.set(items);
        this.isLoading.set(false);
      }),
      catchError((err) => {
        this.isLoading.set(false);
        this.error.set(err.message || 'Failed to load investigation packages.');
        return of([]);
      })
    );
  }

  loadInvestigationById(id: string): Observable<InvestigationResult | null> {
    this.isLoading.set(true);
    this.error.set(null);

    return this.http.get<InvestigationResult>(`${this.baseUrl}/investigations/${id}`).pipe(
      tap((result) => {
        this.selectedInvestigation.set(result);
        this.isLoading.set(false);
      }),
      catchError((err) => {
        this.isLoading.set(false);
        this.error.set(err.message || `Investigation with ID '${id}' could not be loaded.`);
        this.selectedInvestigation.set(null);
        return of(null);
      })
    );
  }

  getGeneratedTest(id: string): Observable<string> {
    return this.http.get(`${this.baseUrl}/investigations/${id}/test`, { responseType: 'text' }).pipe(
      catchError(() => of('// Synthesized test artifact unavailable.'))
    );
  }

  getReportMarkdown(id: string): Observable<string> {
    return this.http.get(`${this.baseUrl}/investigations/${id}/report?format=markdown`, { responseType: 'text' }).pipe(
      catchError(() => of('# Report unavailable'))
    );
  }

  getReportJson(id: string): Observable<Record<string, unknown>> {
    return this.http.get<Record<string, unknown>>(`${this.baseUrl}/investigations/${id}/report?format=json`).pipe(
      catchError(() => of({}))
    );
  }

  getEvidenceGraph(id: string): Observable<import('../models/investigation.models').EvidenceGraph | null> {
    return this.http.get<import('../models/investigation.models').EvidenceGraph>(`${this.baseUrl}/investigations/${id}/evidence-graph`).pipe(
      catchError(() => of(null))
    );
  }

  getInvestigationExplanation(id: string): Observable<import('../models/investigation.models').ForensicInvestigationExplanation | null> {
    return this.http.get<import('../models/investigation.models').ForensicInvestigationExplanation>(`${this.baseUrl}/investigations/${id}/explanation`).pipe(
      catchError(() => of(null))
    );
  }

  replayInvestigation(id: string, analysisVersion: string = 'forensics-v1'): Observable<import('../models/investigation.models').ReplayResult | null> {
    const params = new HttpParams().set('analysis_version', analysisVersion);
    return this.http.post<import('../models/investigation.models').ReplayResult>(`${this.baseUrl}/investigations/${id}/replay`, {}, { params }).pipe(
      catchError(() => of(null))
    );
  }

  compareInvestigations(id: string, otherId: string): Observable<import('../models/investigation.models').InvestigationComparisonResult | null> {
    return this.http.get<import('../models/investigation.models').InvestigationComparisonResult>(`${this.baseUrl}/investigations/${id}/compare/${otherId}`).pipe(
      catchError(() => of(null))
    );
  }

  startInvestigation(request: {
    project_id: string;
    analysis_id: string;
    version_a: { base_url: string; repository_path?: string };
    version_b: { base_url: string; repository_path?: string };
  }): Observable<{ workflow_id: string; analysis_id: string; status: string; message: string } | null> {
    return this.http.post<{ workflow_id: string; analysis_id: string; status: string; message: string }>(
      `${this.baseUrl}/investigations/start`,
      request
    ).pipe(
      catchError((err) => {
        this.error.set(err.message || 'Failed to start investigation workflow.');
        return of(null);
      })
    );
  }

  getWorkflowStatus(workflowId: string): Observable<{
    workflow_id: string;
    analysis_id: string;
    status: string;
    current_phase: string;
    history: Array<{ node_name: string; status: string; duration_ms?: number }>;
    events_count: number;
    error_message?: string | null;
  } | null> {
    return this.http.get<{
      workflow_id: string;
      analysis_id: string;
      status: string;
      current_phase: string;
      history: Array<{ node_name: string; status: string; duration_ms?: number }>;
      events_count: number;
      error_message?: string | null;
    }>(`${this.baseUrl}/investigations/workflow/${workflowId}/status`).pipe(
      catchError(() => of(null))
    );
  }

  setStatusFilter(status: string): void {
    this.statusFilter.set(status);
  }

  setCategoryFilter(category: string): void {
    this.categoryFilter.set(category);
  }

  setSearchQuery(query: string): void {
    this.searchQuery.set(query);
  }

  setActiveTab(tab: string): void {
    this.selectedTab.set(tab);
  }
}

