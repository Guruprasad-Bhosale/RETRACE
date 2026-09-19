import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, of, tap } from 'rxjs';
import { AnalysisSession, Project, SystemStatus } from '../models';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://localhost:8000';

  // Signals for reactive state
  readonly systemStatus = signal<SystemStatus | null>(null);
  readonly isLoadingStatus = signal<boolean>(false);
  readonly statusError = signal<string | null>(null);

  getSystemStatus(): Observable<SystemStatus> {
    this.isLoadingStatus.set(true);
    this.statusError.set(null);
    return this.http.get<SystemStatus>(`${this.baseUrl}/api/v1/system/status`).pipe(
      tap((status) => {
        this.systemStatus.set(status);
        this.isLoadingStatus.set(false);
      }),
      catchError((err) => {
        this.isLoadingStatus.set(false);
        this.statusError.set(err.message || 'Failed to connect to RETRACE API');
        return of({
          environment: 'unknown',
          service_name: 'retrace-api',
          api_status: 'disconnected',
          database_status: 'disconnected',
          redis_status: 'disconnected',
          storage_backend: 'local',
        });
      })
    );
  }

  getProjects(): Observable<Project[]> {
    return this.http.get<Project[]>(`${this.baseUrl}/api/v1/projects`).pipe(
      catchError(() => of([]))
    );
  }

  getAnalyses(): Observable<AnalysisSession[]> {
    return this.http.get<AnalysisSession[]>(`${this.baseUrl}/api/v1/analyses`).pipe(
      catchError(() => of([]))
    );
  }
}
