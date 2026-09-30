import { Component, OnInit, inject } from '@angular/core';
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
    <div class="space-y-6">
      <!-- Top Title Bar -->
      <div class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 class="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <span class="inline-flex h-3 w-3 rounded-full bg-indigo-500"></span>
            Investigation Command Center
          </h1>
          <p class="text-sm text-slate-400 mt-1">
            Autonomous Regression Findings, Causal Replays, Source Attribution & Generated Test Packages
          </p>
        </div>
        <button
          (click)="reload()"
          class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-medium border border-slate-700 transition"
        >
          <span>↻</span> Refresh Investigations
        </button>
      </div>

      <!-- Quick Metrics Grid -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-sm">
          <span class="text-xs font-mono text-slate-400">TOTAL INVESTIGATIONS</span>
          <div class="text-2xl font-bold text-slate-100 mt-1">{{ investigations().length }}</div>
        </div>
        <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-sm">
          <span class="text-xs font-mono text-emerald-400">COMPLETED / LOCATED</span>
          <div class="text-2xl font-bold text-emerald-400 mt-1">{{ completedCount }}</div>
        </div>
        <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-sm">
          <span class="text-xs font-mono text-amber-400">PARTIAL / CANDIDATE</span>
          <div class="text-2xl font-bold text-amber-400 mt-1">{{ partialCount }}</div>
        </div>
        <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 shadow-sm">
          <span class="text-xs font-mono text-purple-400">INCONCLUSIVE</span>
          <div class="text-2xl font-bold text-purple-400 mt-1">{{ inconclusiveCount }}</div>
        </div>
      </div>

      <!-- Search and Filter Controls -->
      <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <!-- Search Input -->
        <div class="flex-1 min-w-[240px]">
          <input
            type="text"
            [ngModel]="searchQuery()"
            (ngModelChange)="service.setSearchQuery($event)"
            placeholder="Search by ID, Category, Title, File or Commit..."
            class="w-full px-3.5 py-2 rounded-lg bg-slate-950 text-xs font-mono text-slate-200 border border-slate-800 focus:outline-none focus:border-indigo-500 placeholder-slate-600 transition"
          />
        </div>

        <!-- Status Filter Tabs -->
        <div class="flex items-center gap-1.5 overflow-x-auto text-xs font-mono">
          <button
            *ngFor="let s of statusOptions"
            (click)="service.setStatusFilter(s)"
            class="px-3 py-1.5 rounded-lg border transition"
            [ngClass]="statusFilter() === s ? 'bg-indigo-600 text-white border-indigo-500 font-bold' : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200'"
          >
            {{ s }}
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div *ngIf="isLoading()" class="p-12 text-center text-slate-400 space-y-3">
        <div class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-500 border-r-transparent"></div>
        <p class="text-xs font-mono">Loading investigation packages...</p>
      </div>

      <!-- Error State -->
      <div *ngIf="error() && !isLoading()" class="p-6 rounded-xl bg-rose-950/40 border border-rose-800 text-center space-y-2">
        <h3 class="text-sm font-bold text-rose-300">Failed to load investigations</h3>
        <p class="text-xs text-rose-400 font-mono">{{ error() }}</p>
      </div>

      <!-- Empty State -->
      <div
        *ngIf="!isLoading() && !error() && filteredList().length === 0"
        class="p-12 rounded-xl bg-slate-900/40 border border-slate-800 text-center space-y-3"
      >
        <span class="text-3xl block">🔍</span>
        <h3 class="text-sm font-bold text-slate-300">No matching investigations found</h3>
        <p class="text-xs text-slate-500 font-mono">
          Try clearing your search query or adjusting your status filter.
        </p>
      </div>

      <!-- Investigations List Table -->
      <div *ngIf="!isLoading() && filteredList().length > 0" class="overflow-hidden rounded-xl bg-slate-900 border border-slate-800 shadow-sm">
        <div class="overflow-x-auto">
          <table class="w-full text-xs text-left">
            <thead>
              <tr class="border-b border-slate-800 text-slate-400 font-mono uppercase text-[11px] bg-slate-950/60">
                <th class="py-3 px-4">INVESTIGATION</th>
                <th class="py-3 px-4">CATEGORY</th>
                <th class="py-3 px-4">STATUS</th>
                <th class="py-3 px-4">ATTRIBUTED SOURCE</th>
                <th class="py-3 px-4">COMMIT</th>
                <th class="py-3 px-4">TEST</th>
                <th class="py-3 px-4 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/80">
              <tr
                *ngFor="let item of filteredList()"
                class="hover:bg-slate-800/50 transition cursor-pointer group"
                [routerLink]="['/investigations', item.investigation_id]"
              >
                <!-- Title and ID -->
                <td class="py-3.5 px-4 font-mono">
                  <span class="font-bold text-slate-100 group-hover:text-indigo-300 transition block text-sm">
                    {{ item.title }}
                  </span>
                  <span class="text-[11px] text-slate-500">
                    ID: {{ item.investigation_id }}
                  </span>
                </td>

                <!-- Category -->
                <td class="py-3.5 px-4 font-mono">
                  <span class="px-2 py-0.5 rounded bg-slate-950 text-indigo-400 font-semibold border border-slate-800">
                    {{ item.category }}
                  </span>
                </td>

                <!-- Status Badge -->
                <td class="py-3.5 px-4">
                  <app-status-badge [status]="item.status"></app-status-badge>
                </td>

                <!-- Source Location -->
                <td class="py-3.5 px-4 font-mono text-slate-300">
                  <span *ngIf="item.source_location" class="truncate block max-w-[200px]">
                    {{ item.source_location }}
                  </span>
                  <span *ngIf="!item.source_location" class="text-slate-600">
                    (Inconclusive)
                  </span>
                </td>

                <!-- Commit Hash -->
                <td class="py-3.5 px-4 font-mono text-slate-400">
                  <span *ngIf="item.commit_hash" class="px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-[11px]">
                    {{ item.commit_hash }}
                  </span>
                  <span *ngIf="!item.commit_hash" class="text-slate-600">-</span>
                </td>

                <!-- Generated Test Status -->
                <td class="py-3.5 px-4 font-mono">
                  <span
                    *ngIf="item.has_generated_test"
                    class="px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800 text-[11px]"
                  >
                    Playwright TS
                  </span>
                  <span
                    *ngIf="!item.has_generated_test"
                    class="text-slate-600 text-[11px]"
                  >
                    None
                  </span>
                </td>

                <!-- Action Button -->
                <td class="py-3.5 px-4 text-right font-mono">
                  <span class="inline-flex items-center gap-1 text-indigo-400 group-hover:text-indigo-300 font-bold transition">
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
}
