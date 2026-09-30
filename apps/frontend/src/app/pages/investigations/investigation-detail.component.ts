import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { InvestigationService } from '../../core/services/investigation.service';
import { StatusBadgeComponent } from './components/status-badge.component';
import { EvidenceChainViewComponent } from './components/evidence-chain-view.component';
import { ReproductionTimelineComponent } from './components/reproduction-timeline.component';
import { AbComparisonViewComponent } from './components/ab-comparison-view.component';
import { SourceDiffViewComponent } from './components/source-diff-view.component';
import { GeneratedTestViewComponent } from './components/generated-test-view.component';
import { ReportViewComponent } from './components/report-view.component';
import { ArtifactViewerComponent } from './components/artifact-viewer.component';

@Component({
  selector: 'app-investigation-detail',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    StatusBadgeComponent,
    EvidenceChainViewComponent,
    ReproductionTimelineComponent,
    AbComparisonViewComponent,
    SourceDiffViewComponent,
    GeneratedTestViewComponent,
    ReportViewComponent,
    ArtifactViewerComponent,
  ],
  template: `
    <div class="space-y-6">
      <!-- Top Navigation & Breadcrumb -->
      <div class="flex items-center justify-between">
        <a
          routerLink="/investigations"
          class="inline-flex items-center gap-2 text-xs font-mono text-slate-400 hover:text-slate-200 transition"
        >
          <span>←</span> Back to Investigations
        </a>
        <div class="flex items-center gap-2 text-xs font-mono text-slate-500">
          <span>INVESTIGATION ID:</span>
          <span class="text-slate-300 font-bold">{{ investigationId() }}</span>
        </div>
      </div>

      <!-- Loading State -->
      <div *ngIf="isLoading()" class="p-12 text-center text-slate-400 space-y-3">
        <div class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-500 border-r-transparent"></div>
        <p class="text-xs font-mono">Loading investigation package...</p>
      </div>

      <!-- Error State -->
      <div *ngIf="error() && !isLoading()" class="p-6 rounded-xl bg-rose-950/40 border border-rose-800 text-center space-y-3">
        <span class="text-2xl block">⚠️</span>
        <h3 class="text-sm font-bold text-rose-300">Unable to load investigation</h3>
        <p class="text-xs text-rose-400 font-mono">{{ error() }}</p>
        <button
          (click)="reload()"
          class="px-4 py-1.5 rounded-lg bg-rose-900 hover:bg-rose-800 text-white text-xs font-mono font-medium transition"
        >
          Retry
        </button>
      </div>

      <!-- Loaded Investigation Workspace -->
      <div *ngIf="investigation() && !isLoading()" class="space-y-6">
        <!-- Main Header Banner -->
        <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-4">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div class="space-y-1.5 max-w-3xl">
              <div class="flex items-center gap-2.5">
                <app-status-badge [status]="investigation()!.status"></app-status-badge>
                <span class="px-2 py-0.5 rounded bg-slate-950 text-indigo-400 text-xs font-mono font-bold border border-slate-800">
                  {{ investigation()!.classification.category }}
                </span>
                <span class="text-xs font-mono text-slate-500">
                  Rule: {{ investigation()!.classification.rule_id }}
                </span>
              </div>
              <h1 class="text-xl font-bold tracking-tight text-white">
                {{ investigation()!.report.title }}
              </h1>
              <p class="text-xs text-slate-400 leading-relaxed">
                {{ investigation()!.classification.reason }}
              </p>
            </div>

            <!-- Quick Action Buttons -->
            <div class="flex items-center gap-2.5 font-mono text-xs">
              <button
                (click)="copyInvestigationId()"
                class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
              >
                {{ idCopied() ? '✓ Copied' : 'Copy ID' }}
              </button>
              <button
                *ngIf="investigation()!.generated_test"
                (click)="activeTab.set('generated-test')"
                class="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-md shadow-indigo-600/20 transition flex items-center gap-1.5"
              >
                <span>🧪 View Test</span>
              </button>
            </div>
          </div>

          <!-- Inconclusive Warning Banner if applicable -->
          <div
            *ngIf="investigation()!.status === 'INCONCLUSIVE'"
            class="p-3.5 rounded-xl bg-purple-950/40 border border-purple-800/60 text-xs text-purple-300 flex items-center gap-3"
          >
            <span class="text-lg">ℹ️</span>
            <div>
              <strong class="font-bold">Investigation Inconclusive:</strong> Available empirical evidence and source diffs were insufficient to authoritatively establish a causal root-cause location.
            </div>
          </div>
        </div>

        <!-- Tab Navigation Bar -->
        <div class="border-b border-slate-800">
          <nav class="flex space-x-2 overflow-x-auto pb-1 text-xs font-mono font-medium">
            <button
              (click)="activeTab.set('overview')"
              class="px-3.5 py-2 rounded-t-lg transition border-b-2"
              [ngClass]="activeTab() === 'overview' ? 'border-indigo-500 text-indigo-400 bg-slate-900/80 font-bold' : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'"
            >
              📌 Overview
            </button>
            <button
              (click)="activeTab.set('reproduction')"
              class="px-3.5 py-2 rounded-t-lg transition border-b-2"
              [ngClass]="activeTab() === 'reproduction' ? 'border-indigo-500 text-indigo-400 bg-slate-900/80 font-bold' : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'"
            >
              🔄 Reproduction
            </button>
            <button
              (click)="activeTab.set('ab-comparison')"
              class="px-3.5 py-2 rounded-t-lg transition border-b-2"
              [ngClass]="activeTab() === 'ab-comparison' ? 'border-indigo-500 text-indigo-400 bg-slate-900/80 font-bold' : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'"
            >
              ⚖️ A/B Comparison
            </button>
            <button
              (click)="activeTab.set('source-diff')"
              class="px-3.5 py-2 rounded-t-lg transition border-b-2"
              [ngClass]="activeTab() === 'source-diff' ? 'border-indigo-500 text-indigo-400 bg-slate-900/80 font-bold' : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'"
            >
              💻 Source & Root Cause
            </button>
            <button
              (click)="activeTab.set('evidence-chain')"
              class="px-3.5 py-2 rounded-t-lg transition border-b-2"
              [ngClass]="activeTab() === 'evidence-chain' ? 'border-indigo-500 text-indigo-400 bg-slate-900/80 font-bold' : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'"
            >
              ⛓ Evidence Chain
            </button>
            <button
              (click)="activeTab.set('generated-test')"
              class="px-3.5 py-2 rounded-t-lg transition border-b-2"
              [ngClass]="activeTab() === 'generated-test' ? 'border-indigo-500 text-indigo-400 bg-slate-900/80 font-bold' : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'"
            >
              🧪 Playwright Test
            </button>
            <button
              (click)="activeTab.set('report')"
              class="px-3.5 py-2 rounded-t-lg transition border-b-2"
              [ngClass]="activeTab() === 'report' ? 'border-indigo-500 text-indigo-400 bg-slate-900/80 font-bold' : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'"
            >
              📄 Evidence Report
            </button>
            <button
              (click)="activeTab.set('artifacts')"
              class="px-3.5 py-2 rounded-t-lg transition border-b-2"
              [ngClass]="activeTab() === 'artifacts' ? 'border-indigo-500 text-indigo-400 bg-slate-900/80 font-bold' : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'"
            >
              📦 Artifacts ({{ investigation()!.artifacts.length }})
            </button>
          </nav>
        </div>

        <!-- Tab Content Views -->
        <div class="py-2">
          <!-- 1. Overview Tab -->
          <div *ngIf="activeTab() === 'overview'" class="space-y-6">
            <!-- 4 Overview Metric Cards -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono">
              <div class="p-4 rounded-xl bg-slate-900 border border-slate-800">
                <span class="text-slate-500 block text-[10px]">CATEGORY</span>
                <span class="font-bold text-slate-100 text-sm mt-1 block">{{ investigation()!.classification.category }}</span>
                <span class="text-slate-500 text-[11px]">Rule: {{ investigation()!.classification.rule_id }}</span>
              </div>

              <div class="p-4 rounded-xl bg-slate-900 border border-slate-800">
                <span class="text-slate-500 block text-[10px]">REPRODUCTION</span>
                <span class="font-bold text-slate-100 text-sm mt-1 block">{{ investigation()!.reproduction?.status || 'NOT_ATTEMPTED' }}</span>
                <span class="text-slate-500 text-[11px]">{{ investigation()!.reproduction?.path?.steps?.length || 0 }} causal steps</span>
              </div>

              <div class="p-4 rounded-xl bg-slate-900 border border-slate-800">
                <span class="text-slate-500 block text-[10px]">ROOT CAUSE</span>
                <span class="font-bold text-slate-100 text-sm mt-1 block">{{ investigation()!.root_cause?.status || 'INCONCLUSIVE' }}</span>
                <span class="text-slate-500 text-[11px]">{{ investigation()!.root_cause?.primary_attribution?.source_location?.symbol_name || 'No symbol' }}</span>
              </div>

              <div class="p-4 rounded-xl bg-slate-900 border border-slate-800">
                <span class="text-slate-500 block text-[10px]">SYNTHESIZED TEST</span>
                <span class="font-bold text-slate-100 text-sm mt-1 block">{{ investigation()!.generated_test?.validation_status || 'INCOMPLETE' }}</span>
                <span class="text-slate-500 text-[11px]">Playwright (TS)</span>
              </div>
            </div>

            <!-- Executive Summary Card -->
            <div class="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
              <h3 class="text-sm font-bold text-slate-200">Executive Summary</h3>
              <p class="text-xs text-slate-300 leading-relaxed">
                {{ investigation()!.report.summary }}
              </p>
            </div>

            <!-- Side-by-side quick diff preview -->
            <app-ab-comparison-view
              [classification]="investigation()!.classification"
              [reproduction]="investigation()!.reproduction || null"
            ></app-ab-comparison-view>
          </div>

          <!-- 2. Reproduction Tab -->
          <div *ngIf="activeTab() === 'reproduction'">
            <app-reproduction-timeline [reproduction]="investigation()!.reproduction || null"></app-reproduction-timeline>
          </div>

          <!-- 3. A/B Comparison Tab -->
          <div *ngIf="activeTab() === 'ab-comparison'">
            <app-ab-comparison-view
              [classification]="investigation()!.classification"
              [reproduction]="investigation()!.reproduction || null"
            ></app-ab-comparison-view>
          </div>

          <!-- 4. Source & Root Cause Tab -->
          <div *ngIf="activeTab() === 'source-diff'">
            <app-source-diff-view [rootCause]="investigation()!.root_cause || null"></app-source-diff-view>
          </div>

          <!-- 5. Evidence Chain Tab -->
          <div *ngIf="activeTab() === 'evidence-chain'">
            <app-evidence-chain-view [evidenceChain]="investigation()!.report.evidence_chain"></app-evidence-chain-view>
          </div>

          <!-- 6. Generated Test Tab -->
          <div *ngIf="activeTab() === 'generated-test'">
            <app-generated-test-view [generatedTest]="investigation()!.generated_test || null"></app-generated-test-view>
          </div>

          <!-- 7. Report Tab -->
          <div *ngIf="activeTab() === 'report'">
            <app-report-view [report]="investigation()!.report"></app-report-view>
          </div>

          <!-- 8. Artifacts Tab -->
          <div *ngIf="activeTab() === 'artifacts'">
            <app-artifact-viewer [artifacts]="investigation()!.artifacts"></app-artifact-viewer>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class InvestigationDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(InvestigationService);

  readonly investigationId = signal<string>('');
  readonly investigation = this.service.selectedInvestigation;
  readonly isLoading = this.service.isLoading;
  readonly error = this.service.error;
  readonly activeTab = this.service.selectedTab;
  readonly idCopied = signal<boolean>(false);

  ngOnInit(): void {
    this.route.paramMap.subscribe((params) => {
      const id = params.get('id');
      if (id) {
        this.investigationId.set(id);
        this.service.loadInvestigationById(id).subscribe();
      }
    });
  }

  reload(): void {
    const id = this.investigationId();
    if (id) {
      this.service.loadInvestigationById(id).subscribe();
    }
  }

  copyInvestigationId(): void {
    const id = this.investigationId();
    if (id) {
      navigator.clipboard.writeText(id);
      this.idCopied.set(true);
      setTimeout(() => this.idCopied.set(false), 2000);
    }
  }
}
