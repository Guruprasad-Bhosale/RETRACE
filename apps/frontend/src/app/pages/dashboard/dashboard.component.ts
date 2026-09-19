import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="space-y-6">
      <!-- Top Title Bar -->
      <div class="flex items-center justify-between border-b border-slate-800 pb-5">
        <div>
          <h1 class="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <span class="inline-flex h-3 w-3 rounded-full bg-emerald-500 animate-pulse"></span>
            RETRACE Autonomous Engineering Platform
          </h1>
          <p class="text-sm text-slate-400 mt-1">
            Autonomous Version A/B Exploration, Behavioral Regression Detection & Root Cause Investigation
          </p>
        </div>
        <button
          (click)="refreshStatus()"
          class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium border border-slate-700 transition"
        >
          <span>↻</span> Refresh Status
        </button>
      </div>

      <!-- System Health Grid -->
      <div>
        <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Platform Subsystem Status (Phase 0 Foundation)
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <!-- API Status Card -->
          <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-medium text-slate-400">FastAPI Server</span>
              <span
                class="px-2 py-0.5 text-xs font-semibold rounded-full"
                [ngClass]="status()?.api_status === 'online' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'"
              >
                {{ status()?.api_status === 'online' ? 'ONLINE' : 'OFFLINE' }}
              </span>
            </div>
            <div class="text-lg font-bold text-slate-100">API Gateway</div>
            <div class="text-xs text-slate-500 mt-1">v0.1.0 • /api/v1</div>
          </div>

          <!-- PostgreSQL Status Card -->
          <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-medium text-slate-400">PostgreSQL</span>
              <span
                class="px-2 py-0.5 text-xs font-semibold rounded-full"
                [ngClass]="status()?.database_status === 'connected' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'"
              >
                {{ status()?.database_status === 'connected' ? 'CONNECTED' : 'STANDBY' }}
              </span>
            </div>
            <div class="text-lg font-bold text-slate-100">SQLAlchemy + Alembic</div>
            <div class="text-xs text-slate-500 mt-1">pgvector ready</div>
          </div>

          <!-- Redis Status Card -->
          <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-medium text-slate-400">Redis Streams</span>
              <span
                class="px-2 py-0.5 text-xs font-semibold rounded-full"
                [ngClass]="status()?.redis_status === 'connected' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-amber-950 text-amber-400 border border-amber-800'"
              >
                {{ status()?.redis_status === 'connected' ? 'CONNECTED' : 'STANDBY' }}
              </span>
            </div>
            <div class="text-lg font-bold text-slate-100">Worker Event Bus</div>
            <div class="text-xs text-slate-500 mt-1">Async Queue Pipeline</div>
          </div>

          <!-- Artifact Storage Card -->
          <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-medium text-slate-400">Artifact Persistence</span>
              <span class="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-950 text-blue-400 border border-blue-800 uppercase">
                {{ status()?.storage_backend || 'LOCAL' }}
              </span>
            </div>
            <div class="text-lg font-bold text-slate-100">Multi-Modal Store</div>
            <div class="text-xs text-slate-500 mt-1">MinIO / S3 Abstraction</div>
          </div>
        </div>
      </div>

      <!-- Core Architecture Roadmap Summary -->
      <div class="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
        <h3 class="text-sm font-semibold text-slate-200 mb-2">Phase 0 Engineering Baseline Initialized</h3>
        <p class="text-xs text-slate-400 leading-relaxed">
          Clean boundaries established between Angular 22+ frontend, FastAPI orchestration gateway, pure domain contracts,
          async database session pooling, Redis Streams connectivity, and pluggable storage providers.
        </p>
      </div>
    </div>
  `
})
export class DashboardComponent implements OnInit {
  private readonly api = inject(ApiService);
  readonly status = this.api.systemStatus;

  ngOnInit(): void {
    this.refreshStatus();
  }

  refreshStatus(): void {
    this.api.getSystemStatus().subscribe();
  }
}
