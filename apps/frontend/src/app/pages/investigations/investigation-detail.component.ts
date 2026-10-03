import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { InvestigationService } from '../../core/services/investigation.service';
import { ForensicInteractionService, ForensicTimelineStage } from '../../core/services/forensic-interaction.service';
import { EvidenceGraph, ForensicInvestigationExplanation } from '../../core/models/investigation.models';
import { StatusBadgeComponent } from './components/status-badge.component';
import { EvidenceChainViewComponent } from './components/evidence-chain-view.component';
import { ReproductionTimelineComponent } from './components/reproduction-timeline.component';
import { AbComparisonViewComponent } from './components/ab-comparison-view.component';
import { SourceDiffViewComponent } from './components/source-diff-view.component';
import { GeneratedTestViewComponent } from './components/generated-test-view.component';
import { ReportViewComponent } from './components/report-view.component';
import { ArtifactViewerComponent } from './components/artifact-viewer.component';
import { EvidenceGraphViewComponent } from './components/evidence-graph-view.component';
import { HypothesesViewComponent } from './components/hypotheses-view.component';
import { InvestigationReplayComparisonComponent } from './components/investigation-replay-comparison.component';

export interface InvestigationTimelineItem {
  stage: ForensicTimelineStage;
  label: string;
  status: 'COMPLETE' | 'ACTIVE' | 'PENDING' | 'FAILED';
  description: string;
}

@Component({
  selector: 'app-investigation-detail',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    StatusBadgeComponent,
    ReproductionTimelineComponent,
    AbComparisonViewComponent,
    SourceDiffViewComponent,
    GeneratedTestViewComponent,
    ReportViewComponent,
    ArtifactViewerComponent,
    EvidenceGraphViewComponent,
    HypothesesViewComponent,
    InvestigationReplayComparisonComponent,
  ],
  template: `
    <div class="space-y-6 page-enter font-mono">
      <!-- Top Navigation & Breadcrumb Header -->
      <div class="flex items-center justify-between border-b border-(--grid) pb-3 text-xs">
        <a
          routerLink="/investigations"
          class="inline-flex items-center gap-2 text-(--muted) hover:text-(--or) transition no-underline cursor-pointer"
        >
          <span>&larr;</span> Back to Investigations
        </a>
        <div class="flex items-center gap-2 text-(--muted)">
          <span>CASE ID:</span>
          <span class="text-(--ink) font-bold">{{ investigationId() }}</span>
        </div>
      </div>

      <!-- Loading State -->
      <div *ngIf="isLoading() && !investigation()" class="p-12 bento-card border border-(--grid) text-center space-y-3">
        <div class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-(--or) border-r-transparent"></div>
        <div class="text-xs text-(--muted)">Loading case file & reconstructing evidence DAG...</div>
      </div>

      <!-- Error State -->
      <div *ngIf="error() && !investigation()" class="p-6 rounded bento-card border border-rose-800 text-center space-y-3">
        <span class="text-2xl block">⚠️</span>
        <h3 class="text-sm font-bold text-rose-500 uppercase">Unable to load investigation package</h3>
        <p class="text-xs text-(--muted)">{{ error() }}</p>
        <button (click)="reload()" class="btn-retrace text-xs cursor-pointer">
          Retry
        </button>
      </div>

      <!-- Loaded Investigation Workspace -->
      <div *ngIf="investigation()" class="space-y-6">
        
        <!-- 1. Executive Summary & Narrative Header (5-Second Comprehension) -->
        <div class="p-6 rounded bento-card border border-(--grid) space-y-4">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div class="space-y-2 max-w-3xl">
              <div class="flex flex-wrap items-center gap-2.5 text-xs">
                <app-status-badge [status]="investigation()!.status"></app-status-badge>
                <span class="px-2 py-0.5 rounded bento-card-elevated text-(--or) font-bold border border-(--grid)">
                  {{ investigation()!.classification.category }}
                </span>
                <span class="text-(--muted)">
                  Rule: <strong class="text-(--ink)">{{ investigation()!.classification.rule_id }}</strong>
                </span>
              </div>
              
              <h1 class="text-xl font-bold tracking-tight text-(--ink) uppercase">
                {{ investigation()!.report.title }}
              </h1>
              
              <p class="text-xs text-(--muted) leading-relaxed">
                {{ investigation()!.classification.reason }}
              </p>
            </div>

            <!-- Header Action Toolbar -->
            <div class="flex flex-wrap items-center gap-2 text-xs">
              <button
                (click)="copyInvestigationId()"
                class="px-3 py-1.5 rounded bento-card-elevated hover:border-(--or) text-(--ink) transition cursor-pointer"
                title="Copy Investigation ID"
              >
                {{ idCopied() ? '✓ Copied' : 'Copy ID' }}
              </button>
              <button
                (click)="exportMarkdownReport()"
                class="px-3 py-1.5 rounded bento-card-elevated hover:border-(--or) text-(--ink) transition cursor-pointer flex items-center gap-1.5"
                title="Export Markdown Report"
              >
                <span>📄 Export MD</span>
              </button>
              <button
                (click)="exportJsonReport()"
                class="px-3 py-1.5 rounded bento-card-elevated hover:border-(--or) text-(--ink) transition cursor-pointer flex items-center gap-1.5"
                title="Export JSON Report"
              >
                <span>📦 Export JSON</span>
              </button>
            </div>
          </div>

          <!-- A -> B Behavioral Divergence Summary Card -->
          <div class="p-4 rounded bento-card-elevated border border-(--grid) space-y-2.5">
            <div class="text-[10px] text-(--muted) uppercase font-bold tracking-wider flex items-center justify-between">
              <span class="flex items-center gap-1.5">
                <span class="inline-block w-1.5 h-1.5 rounded-full bg-(--or)"></span>
                Causal Regression Trajectory (Baseline vs Regressed)
              </span>
              <span class="text-emerald-500 font-bold">EMPIRICALLY VERIFIED</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
              <div class="p-3 rounded bento-card border border-emerald-800/50 bg-emerald-950/20 space-y-1">
                <div class="text-[9px] text-emerald-400 font-bold uppercase">VERSION A (BASELINE EXPECTED)</div>
                <div class="font-bold text-(--ink)">Expected Behavior</div>
                <div class="text-[11px] text-(--muted) truncate">
                  {{ investigation()!.classification.evidence?.details?.['text_a'] || 'Standard Interactive State' }}
                </div>
              </div>

              <div class="p-3 rounded bento-card border border-(--or) bg-orange-500/10 space-y-1">
                <div class="text-[9px] text-(--or) font-bold uppercase">EMPIRICAL DIVERGENCE</div>
                <div class="font-bold text-(--or)">{{ investigation()!.classification.rule_id }}</div>
                <div class="text-[11px] text-(--muted) truncate">
                  Subject: {{ investigation()!.classification.evidence?.canonical_subject || 'Observed Defect' }}
                </div>
              </div>

              <div class="p-3 rounded bento-card border border-rose-800/50 bg-rose-950/20 space-y-1">
                <div class="text-[9px] text-rose-400 font-bold uppercase">VERSION B (CANDIDATE REGRESSION)</div>
                <div class="font-bold text-(--ink)">Regressed Behavior</div>
                <div class="text-[11px] text-(--muted) truncate">
                  {{ investigation()!.classification.evidence?.details?.['text_b'] || investigation()!.classification.reason }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 2. High-Signal Tab Navigation -->
        <div class="border-b border-(--grid)">
          <nav class="flex space-x-2 overflow-x-auto pb-1 text-xs font-medium">
            <button
              (click)="setTab('evidence-graph')"
              class="px-4 py-2 rounded-t transition border-b-2 cursor-pointer"
              [ngClass]="activeTab() === 'evidence-graph' ? 'border-(--or) text-(--or) bg-(--surface) font-bold' : 'border-transparent text-(--muted) hover:text-(--ink)'"
            >
              📊 Evidence Graph
            </button>
            <button
              (click)="setTab('hypotheses')"
              class="px-4 py-2 rounded-t transition border-b-2 cursor-pointer"
              [ngClass]="activeTab() === 'hypotheses' ? 'border-(--or) text-(--or) bg-(--surface) font-bold' : 'border-transparent text-(--muted) hover:text-(--ink)'"
            >
              💡 Hypotheses & Falsification
            </button>
            <button
              (click)="setTab('source-diff')"
              class="px-4 py-2 rounded-t transition border-b-2 cursor-pointer"
              [ngClass]="activeTab() === 'source-diff' ? 'border-(--or) text-(--or) bg-(--surface) font-bold' : 'border-transparent text-(--muted) hover:text-(--ink)'"
            >
              💻 Root Cause & Diff
            </button>
            <button
              (click)="setTab('reproduction')"
              class="px-4 py-2 rounded-t transition border-b-2 cursor-pointer"
              [ngClass]="activeTab() === 'reproduction' ? 'border-(--or) text-(--or) bg-(--surface) font-bold' : 'border-transparent text-(--muted) hover:text-(--ink)'"
            >
              🔄 Reproduction & Test
            </button>
            <button
              (click)="setTab('replay-compare')"
              class="px-4 py-2 rounded-t transition border-b-2 cursor-pointer"
              [ngClass]="activeTab() === 'replay-compare' ? 'border-(--or) text-(--or) bg-(--surface) font-bold' : 'border-transparent text-(--muted) hover:text-(--ink)'"
            >
              ⚡ Replay & Verification
            </button>
            <button
              (click)="setTab('artifacts')"
              class="px-4 py-2 rounded-t transition border-b-2 cursor-pointer"
              [ngClass]="activeTab() === 'artifacts' ? 'border-(--or) text-(--or) bg-(--surface) font-bold' : 'border-transparent text-(--muted) hover:text-(--ink)'"
            >
              📦 Artifacts ({{ investigation()!.artifacts.length }})
            </button>
          </nav>
        </div>

        <!-- 3. Focused Tab Content Panels (Zero Overlap / Zero Redundant Nesting) -->
        <div class="py-2">
          
          <!-- TAB 1: EVIDENCE GRAPH -->
          <div *ngIf="activeTab() === 'evidence-graph'">
            <app-evidence-graph-view
              [graph]="evidenceGraph()"
              [investigation]="investigation()"
              [explanation]="explanation()"
            ></app-evidence-graph-view>
          </div>

          <!-- TAB 2: HYPOTHESES & FALSIFICATION -->
          <div *ngIf="activeTab() === 'hypotheses'" class="space-y-6">
            <app-hypotheses-view
              [explanation]="explanation()"
              [graph]="evidenceGraph()"
            ></app-hypotheses-view>
            <app-ab-comparison-view
              [classification]="investigation()!.classification"
              [reproduction]="investigation()!.reproduction || null"
            ></app-ab-comparison-view>
          </div>

          <!-- TAB 3: ROOT CAUSE & SOURCE DIFF -->
          <div *ngIf="activeTab() === 'source-diff'">
            <app-source-diff-view
              [rootCause]="investigation()!.root_cause || null"
            ></app-source-diff-view>
          </div>

          <!-- TAB 4: REPRODUCTION & SYNTHESIZED TEST -->
          <div *ngIf="activeTab() === 'reproduction'" class="space-y-6">
            <app-reproduction-timeline
              [reproduction]="investigation()!.reproduction || null"
            ></app-reproduction-timeline>
            <app-generated-test-view
              [generatedTest]="investigation()!.generated_test || null"
            ></app-generated-test-view>
          </div>

          <!-- TAB 5: REPLAY & DETERMINISTIC COMPARISON -->
          <div *ngIf="activeTab() === 'replay-compare'">
            <app-investigation-replay-comparison
              [investigationId]="investigationId()"
            ></app-investigation-replay-comparison>
          </div>

          <!-- TAB 6: ARTIFACTS & FULL REPORT -->
          <div *ngIf="activeTab() === 'artifacts'" class="space-y-6">
            <app-artifact-viewer
              [artifacts]="investigation()!.artifacts"
            ></app-artifact-viewer>
            <app-report-view
              [report]="investigation()!.report"
            ></app-report-view>
          </div>

        </div>

      </div>
    </div>
  `,
})
export class InvestigationDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(InvestigationService);
  readonly forensic = inject(ForensicInteractionService);

  readonly investigation = this.service.selectedInvestigation;
  readonly isLoading = this.service.isLoading;
  readonly error = this.service.error;
  readonly evidenceGraph = signal<EvidenceGraph | null>(null);
  readonly explanation = signal<ForensicInvestigationExplanation | null>(null);

  readonly activeTab = signal<string>('evidence-graph');
  readonly idCopied = signal<boolean>(false);
  readonly investigationId = signal<string>('');

  ngOnInit(): void {
    this.route.paramMap.subscribe((params) => {
      const id = params.get('id');
      if (id) {
        this.investigationId.set(id);
        this.service.loadInvestigationById(id).subscribe((res) => {
          if (res) {
            this.service.getEvidenceGraph(id).subscribe((g) => this.evidenceGraph.set(g));
            this.service.getInvestigationExplanation(id).subscribe((e) => this.explanation.set(e));
          }
        });
      }
    });
  }

  setTab(tab: string): void {
    this.activeTab.set(tab);
  }

  copyInvestigationId(): void {
    const id = this.investigationId();
    if (id) {
      this.idCopied.set(true);
      if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(id).catch(() => {});
      }
      setTimeout(() => this.idCopied.set(false), 2000);
    }
  }

  exportMarkdownReport(): void {
    const inv = this.investigation();
    if (!inv) return;
    const md = `# RETRACE Forensic Investigation Report: ${inv.investigation_id}\n\n**Title**: ${inv.report.title}\n**Status**: ${inv.status}\n**Category**: ${inv.classification.category}\n**Rule**: ${inv.classification.rule_id}\n\n## Conclusion\n${inv.classification.reason}\n\n## Attributed Root Cause\n${inv.root_cause?.primary_attribution?.source_location?.file_path || 'None'}:${inv.root_cause?.primary_attribution?.source_location?.start_line || 0}\n`;
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${inv.investigation_id}_report.md`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  exportJsonReport(): void {
    const inv = this.investigation();
    if (!inv) return;
    const json = JSON.stringify(inv, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${inv.investigation_id}_report.json`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  reload(): void {
    const id = this.investigationId();
    if (id) {
      this.service.loadInvestigationById(id).subscribe((res) => {
        if (res) {
          this.service.getEvidenceGraph(id).subscribe((g) => this.evidenceGraph.set(g));
          this.service.getInvestigationExplanation(id).subscribe((e) => this.explanation.set(e));
        }
      });
    }
  }
}
