import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { InvestigationService } from '../../core/services/investigation.service';
import { StatusBadgeComponent } from './components/status-badge.component';

@Component({
  selector: 'app-investigations',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, StatusBadgeComponent],
  template: `
    <div class="space-y-8 animate-reveal font-mono">
      <!-- Top Title Bar with Editorial Context -->
      <div class="flex flex-wrap items-center justify-between gap-4 border-b border-(--grid) pb-6">
        <div>
          <div class="text-[10px] tracking-widest text-(--or) uppercase mb-1 flex items-center gap-2">
            <span class="inline-block w-1.5 h-1.5 rounded-full bg-(--or) animate-pulse"></span>
            04 / FORENSIC CASE FILES
          </div>
          <h1 class="text-3xl sm:text-4xl font-black tracking-tight text-(--ink) uppercase">
            Investigation Command Center
          </h1>
          <p class="text-xs text-(--muted) mt-1 max-w-3xl leading-relaxed">
            Autonomous regression verification, empirical evidence extraction, deterministic replay verification, and synthesized Playwright test packages.
          </p>
        </div>
        <div class="flex items-center gap-3">
          <button
            (click)="reload()"
            class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded bento-card-elevated hover:border-(--or) text-(--ink) text-xs font-medium transition cursor-pointer"
            aria-label="Refresh investigations list"
          >
            <span>↻</span> Refresh Records
          </button>
        </div>
      </div>

      <!-- Bento Autonomous Investigation Launcher (Section 5 Standard) -->
      <div class="bento-card p-6 border border-(--grid) space-y-4">
        <div class="flex flex-wrap items-center justify-between gap-2 border-b border-(--grid) pb-3">
          <div class="flex items-center gap-2 text-xs font-bold text-(--ink) uppercase tracking-wider">
            <span class="text-(--or)">⚡</span>
            <span>Launch Autonomous Regression Investigation</span>
          </div>
          <span class="text-[10px] text-(--muted) uppercase">
            LangGraph Dual-Browser Sensor Pipeline
          </span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
          <!-- Baseline Version A Input -->
          <div class="md:col-span-4 space-y-1.5">
            <label class="text-[10px] text-(--muted) uppercase font-bold flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>
              Version A (Baseline URL)
            </label>
            <input
              type="text"
              [(ngModel)]="versionAUrl"
              placeholder="http://localhost:3001"
              class="w-full px-3.5 py-2 rounded bento-card-elevated text-xs text-(--ink) border border-(--grid) focus:outline-none focus:border-(--or) placeholder-(--muted) transition"
            />
          </div>

          <!-- Target Version B Input -->
          <div class="md:col-span-4 space-y-1.5">
            <label class="text-[10px] text-(--muted) uppercase font-bold flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-(--or) inline-block"></span>
              Version B (Candidate Release URL)
            </label>
            <input
              type="text"
              [(ngModel)]="versionBUrl"
              placeholder="http://localhost:3002"
              class="w-full px-3.5 py-2 rounded bento-card-elevated text-xs text-(--ink) border border-(--grid) focus:outline-none focus:border-(--or) placeholder-(--muted) transition"
            />
          </div>

          <!-- Run Investigation Button -->
          <div class="md:col-span-4">
            <button
              (click)="triggerInvestigation()"
              [disabled]="isLaunching()"
              class="w-full btn-retrace justify-center py-2 text-xs cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span *ngIf="!isLaunching()">▶ START INVESTIGATION</span>
              <span *ngIf="isLaunching()" class="flex items-center gap-2">
                <span class="inline-block w-3 h-3 rounded-full border-2 border-solid border-stone-900 border-r-transparent animate-spin"></span>
                RUNNING INVESTIGATION...
              </span>
            </button>
          </div>
        </div>

        <!-- Inline Live Workflow Execution Feedback -->
        <div *ngIf="workflowFeedback()" class="p-3.5 rounded bento-card-elevated border border-(--or) bg-orange-500/10 text-xs space-y-1.5">
          <div class="flex items-center justify-between text-[11px] font-bold">
            <span class="text-(--or) uppercase flex items-center gap-2">
              <span class="inline-block w-2 h-2 rounded-full bg-(--or) animate-ping"></span>
              Active Workflow: {{ activeWorkflowId() }}
            </span>
            <span class="text-(--ink) uppercase">Phase: {{ workflowPhase() }}</span>
          </div>
          <div class="text-[11px] text-(--muted)">
            {{ workflowFeedback() }}
          </div>
        </div>
      </div>

      <!-- Quick Metrics Grid -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="bento-card p-4">
          <span class="text-[10px] text-(--muted) uppercase font-bold">TOTAL INVESTIGATIONS</span>
          <div class="text-2xl font-black text-(--ink) mt-1">{{ investigations().length }}</div>
        </div>
        <div class="bento-card p-4">
          <span class="text-[10px] text-emerald-500 uppercase font-bold">COMPLETED / LOCATED</span>
          <div class="text-2xl font-black text-emerald-500 mt-1">{{ completedCount }}</div>
        </div>
        <div class="bento-card p-4">
          <span class="text-[10px] text-amber-500 uppercase font-bold">PARTIAL / CANDIDATE</span>
          <div class="text-2xl font-black text-amber-500 mt-1">{{ partialCount }}</div>
        </div>
        <div class="bento-card p-4">
          <span class="text-[10px] text-purple-400 uppercase font-bold">INCONCLUSIVE</span>
          <div class="text-2xl font-black text-purple-400 mt-1">{{ inconclusiveCount }}</div>
        </div>
      </div>

      <!-- Search and Filter Controls -->
      <div class="bento-card p-4 flex flex-wrap items-center justify-between gap-4">
        <!-- Search Input -->
        <div class="flex-1 min-w-[240px]">
          <input
            type="text"
            [ngModel]="searchQuery()"
            (ngModelChange)="service.setSearchQuery($event)"
            placeholder="Search by ID, Category, Title, File or Commit..."
            class="w-full px-3.5 py-2 rounded bento-card-elevated text-xs text-(--ink) border border-(--grid) focus:outline-none focus:border-(--or) placeholder-(--muted) transition"
          />
        </div>

        <!-- Status Filter Tabs -->
        <div class="flex items-center gap-1.5 overflow-x-auto text-xs">
          <button
            *ngFor="let s of statusOptions"
            (click)="service.setStatusFilter(s)"
            class="px-3 py-1.5 rounded border transition font-bold cursor-pointer"
            [ngClass]="statusFilter() === s ? 'bg-(--or) text-[#101010] border-(--or)' : 'bento-card-elevated text-(--muted) border-(--grid) hover:text-(--ink)'"
          >
            {{ s }}
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div *ngIf="isLoading()" class="p-12 text-center text-(--muted) space-y-3">
        <div class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-(--or) border-r-transparent"></div>
        <p class="text-xs">Loading empirical investigation packages...</p>
      </div>

      <!-- Error State -->
      <div *ngIf="error() && !isLoading()" class="p-6 rounded bento-card border-rose-800 text-center space-y-2">
        <h3 class="text-sm font-bold text-rose-400">Failed to load investigations</h3>
        <p class="text-xs text-rose-500">{{ error() }}</p>
      </div>

      <!-- Empty State -->
      <div
        *ngIf="!isLoading() && !error() && filteredList().length === 0"
        class="p-12 rounded bento-card text-center space-y-3"
      >
        <span class="text-3xl block">🔍</span>
        <h3 class="text-sm font-bold text-(--ink) uppercase">No matching investigations found</h3>
        <p class="text-xs text-(--muted)">
          Try clearing your search query or adjusting your status filter.
        </p>
      </div>

      <!-- Investigations List Table -->
      <div *ngIf="!isLoading() && filteredList().length > 0" class="overflow-hidden rounded bento-card shadow-sm border border-(--grid)">
        <div class="overflow-x-auto">
          <table class="w-full text-xs text-left">
            <thead>
              <tr class="border-b border-(--grid) text-(--muted) uppercase text-[10px] bg-(--surface) tracking-wider">
                <th class="py-3 px-4">INVESTIGATION</th>
                <th class="py-3 px-4">CATEGORY</th>
                <th class="py-3 px-4">STATUS</th>
                <th class="py-3 px-4">ATTRIBUTED SOURCE</th>
                <th class="py-3 px-4">COMMIT</th>
                <th class="py-3 px-4">TEST</th>
                <th class="py-3 px-4 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-(--grid)">
              <tr
                *ngFor="let item of filteredList()"
                class="hover:bg-(--surface) transition cursor-pointer group"
                [routerLink]="['/investigations', item.investigation_id]"
              >
                <!-- Title and ID -->
                <td class="py-3.5 px-4">
                  <span class="font-bold text-(--ink) group-hover:text-(--or) transition block text-sm">
                    {{ item.title }}
                  </span>
                  <span class="text-[10px] text-(--muted) tracking-wider">
                    ID: {{ item.investigation_id }}
                  </span>
                </td>

                <!-- Category -->
                <td class="py-3.5 px-4">
                  <span class="px-2 py-0.5 rounded bento-card-elevated text-(--or) font-bold text-[10px] border border-(--grid)">
                    {{ item.category }}
                  </span>
                </td>

                <!-- Status Badge -->
                <td class="py-3.5 px-4">
                  <app-status-badge [status]="item.status"></app-status-badge>
                </td>

                <!-- Source Location -->
                <td class="py-3.5 px-4 text-(--ink)">
                  <span *ngIf="item.source_location" class="truncate block max-w-[220px] font-bold">
                    {{ item.source_location }}
                  </span>
                  <span *ngIf="!item.source_location" class="text-(--muted)">
                    (Inconclusive)
                  </span>
                </td>

                <!-- Commit Hash -->
                <td class="py-3.5 px-4 text-(--muted)">
                  <span *ngIf="item.commit_hash" class="px-1.5 py-0.5 rounded bento-card-elevated text-[11px] font-bold text-(--ink)">
                    {{ item.commit_hash }}
                  </span>
                  <span *ngIf="!item.commit_hash" class="text-(--muted)">-</span>
                </td>

                <!-- Generated Test Status -->
                <td class="py-3.5 px-4">
                  <span
                    *ngIf="item.has_generated_test"
                    class="px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800 text-[10px] font-bold"
                  >
                    Playwright TS
                  </span>
                  <span
                    *ngIf="!item.has_generated_test"
                    class="text-(--muted) text-[10px]"
                  >
                    None
                  </span>
                </td>

                <!-- Action Button -->
                <td class="py-3.5 px-4 text-right">
                  <span class="inline-flex items-center gap-1 text-(--or) group-hover:translate-x-1 font-bold transition-transform text-xs">
                    Inspect <span>→</span>
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
})
export class InvestigationsComponent implements OnInit {
  readonly service = inject(InvestigationService);

  readonly statusOptions = ['ALL', 'COMPLETED', 'PARTIAL', 'INCONCLUSIVE', 'FAILED'];
  readonly investigations = this.service.investigations;
  readonly filteredList = this.service.filteredInvestigations;
  readonly isLoading = this.service.isLoading;
  readonly error = this.service.error;
  readonly statusFilter = this.service.statusFilter;
  readonly searchQuery = this.service.searchQuery;

  // Launcher State
  versionAUrl = 'http://localhost:3001';
  versionBUrl = 'http://localhost:3002';
  readonly isLaunching = signal<boolean>(false);
  readonly activeWorkflowId = signal<string | null>(null);
  readonly workflowPhase = signal<string>('IDLE');
  readonly workflowFeedback = signal<string | null>(null);

  get completedCount(): number {
    return this.investigations().filter((i) => i.status === 'COMPLETED').length;
  }

  get partialCount(): number {
    return this.investigations().filter((i) => i.status === 'PARTIAL').length;
  }

  get inconclusiveCount(): number {
    return this.investigations().filter((i) => i.status === 'INCONCLUSIVE').length;
  }

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    this.service.loadInvestigations().subscribe();
  }

  triggerInvestigation(): void {
    if (!this.versionAUrl || !this.versionBUrl) {
      return;
    }

    this.isLaunching.set(true);
    this.workflowFeedback.set('Initiating dual-version exploration and sensor calibration...');
    this.workflowPhase.set('STARTING');

    const analysisId = '00000000-0000-0000-0000-' + Math.floor(100000000000 + Math.random() * 900000000000);
    this.service
      .startInvestigation({
        project_id: 'commerce-lab-investigation',
        analysis_id: analysisId,
        version_a: { base_url: this.versionAUrl, repository_path: 'lab/applications/commerce/v1' },
        version_b: { base_url: this.versionBUrl, repository_path: 'lab/applications/commerce/v2' },
      })
      .subscribe((res) => {
        if (res && res.workflow_id) {
          this.activeWorkflowId.set(res.workflow_id);
          this.workflowPhase.set('EXPLORING');
          this.workflowFeedback.set(
            `Workflow active (${res.workflow_id}). Autonomous dual-browser sensor executing observations...`
          );
          this.pollWorkflow(res.workflow_id);
        } else {
          this.isLaunching.set(false);
          this.workflowFeedback.set('Investigation triggered. Refreshing case file index...');
          setTimeout(() => {
            this.reload();
            this.workflowFeedback.set(null);
          }, 2000);
        }
      });
  }

  private pollWorkflow(workflowId: string): void {
    const interval = setInterval(() => {
      this.service.getWorkflowStatus(workflowId).subscribe((status) => {
        if (status) {
          this.workflowPhase.set(status.current_phase || status.status);
          if (status.status === 'COMPLETED' || status.status === 'FAILED' || status.status === 'INCONCLUSIVE') {
            clearInterval(interval);
            this.isLaunching.set(false);
            this.workflowFeedback.set(
              `Investigation workflow completed with status [${status.status}]. Updating case files...`
            );
            this.reload();
            setTimeout(() => this.workflowFeedback.set(null), 4000);
          }
        } else {
          clearInterval(interval);
          this.isLaunching.set(false);
          this.reload();
        }
      });
    }, 1500);
  }
}
