import { Component, Input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EvidenceReport } from '../../../core/models/investigation.models';
import { StatusBadgeComponent } from './status-badge.component';

@Component({
  selector: 'app-report-view',
  standalone: true,
  imports: [CommonModule, StatusBadgeComponent],
  template: `
    <div class="space-y-6">
      <!-- Report Header Card -->
      <div class="p-5 rounded-xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div class="space-y-1">
          <div class="flex items-center gap-3">
            <h3 class="text-base font-bold text-slate-100">{{ report?.title || 'Investigation Report' }}</h3>
            <app-status-badge [status]="report?.status || 'PARTIAL'"></app-status-badge>
          </div>
          <p class="text-xs text-slate-400">
            {{ report?.summary || 'Comprehensive evidence-backed investigation report.' }}
          </p>
        </div>

        <!-- Mode Toggle & Actions -->
        <div class="flex items-center gap-3">
          <!-- Format Switcher -->
          <div class="p-1 rounded-lg bg-slate-950 border border-slate-800 flex text-xs font-mono">
            <button
              (click)="formatMode.set('markdown')"
              class="px-2.5 py-1 rounded transition"
              [ngClass]="formatMode() === 'markdown' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'"
            >
              Markdown
            </button>
            <button
              (click)="formatMode.set('json')"
              class="px-2.5 py-1 rounded transition"
              [ngClass]="formatMode() === 'json' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'"
            >
              JSON
            </button>
          </div>

          <button
            (click)="copyReportContent()"
            class="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-medium border border-slate-700 transition"
          >
            {{ copied() ? '✓ Copied' : '📋 Copy' }}
          </button>
          <button
            (click)="downloadReport()"
            class="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-mono font-medium shadow-md shadow-indigo-600/20 transition"
          >
            💾 Download
          </button>
        </div>
      </div>

      <!-- Markdown View -->
      <div *ngIf="formatMode() === 'markdown'" class="space-y-4">
        <div
          *ngFor="let sec of report?.sections || []"
          class="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-2"
        >
          <div class="flex items-center justify-between border-b border-slate-800 pb-2">
            <h4 class="text-sm font-bold text-slate-100">{{ sec.title }}</h4>
            <span *ngIf="sec.evidence_ids.length > 0" class="text-[11px] font-mono text-slate-500">
              Refs: {{ sec.evidence_ids.join(', ') }}
            </span>
          </div>
          <div class="text-xs text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">
            {{ sec.content_markdown }}
          </div>
        </div>
      </div>

      <!-- JSON View -->
      <div *ngIf="formatMode() === 'json'" class="p-4 rounded-xl bg-slate-950 border border-slate-800">
        <pre class="font-mono text-xs text-slate-300 overflow-x-auto p-2 leading-relaxed whitespace-pre">{{ formattedJson }}</pre>
      </div>
    </div>
  `,
})
export class ReportViewComponent {
  @Input() report: EvidenceReport | null = null;
  readonly formatMode = signal<'markdown' | 'json'>('markdown');
  readonly copied = signal<boolean>(false);

  get formattedJson(): string {
    if (!this.report) return '{}';
    return JSON.stringify(this.report.json_content || this.report, null, 2);
  }

  copyReportContent(): void {
    const text =
      this.formatMode() === 'markdown'
        ? this.report?.markdown_content || ''
        : this.formattedJson;
    navigator.clipboard.writeText(text);
    this.copied.set(true);
    setTimeout(() => this.copied.set(false), 2000);
  }

  downloadReport(): void {
    const isMd = this.formatMode() === 'markdown';
    const content = isMd ? this.report?.markdown_content || '' : this.formattedJson;
    const mime = isMd ? 'text/markdown' : 'application/json';
    const ext = isMd ? 'md' : 'json';

    const blob = new Blob([content], { type: mime });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `investigation_report_${this.report?.report_id || 'export'}.${ext}`;
    a.click;
    a.click();
    window.URL.revokeObjectURL(url);
  }
}
