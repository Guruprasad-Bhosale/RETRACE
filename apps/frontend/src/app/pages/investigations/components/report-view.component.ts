import { Component, Input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EvidenceReport } from '../../../core/models/investigation.models';
import { StatusBadgeComponent } from './status-badge.component';

@Component({
  selector: 'app-report-view',
  standalone: true,
  imports: [CommonModule, StatusBadgeComponent],
  styles: [':host { display: block; }'],
  template: `

    <div class="space-y-6 font-mono">
      <!-- Report Header Card -->
      <div class="p-5 rounded bento-card border border-(--grid) flex flex-wrap items-center justify-between gap-4">
        <div class="space-y-1">
          <div class="flex items-center gap-3">
            <h3 class="text-base font-bold text-(--ink) uppercase">{{ report?.title || 'Investigation Report' }}</h3>
            <app-status-badge [status]="report?.status || 'PARTIAL'"></app-status-badge>
          </div>
          <p class="text-xs text-(--muted)">
            {{ report?.summary || 'Comprehensive evidence-backed investigation report.' }}
          </p>
        </div>

        <!-- Mode Toggle & Actions -->
        <div class="flex items-center gap-2">
          <!-- Format Switcher -->
          <div class="p-1 rounded bento-card-elevated border border-(--grid) flex text-xs">
            <button
              (click)="formatMode.set('markdown')"
              class="px-2.5 py-1 rounded transition cursor-pointer"
              [ngClass]="formatMode() === 'markdown' ? 'btn-retrace font-bold' : 'text-(--muted) hover:text-(--ink)'"
            >
              Markdown
            </button>
            <button
              (click)="formatMode.set('json')"
              class="px-2.5 py-1 rounded transition cursor-pointer"
              [ngClass]="formatMode() === 'json' ? 'btn-retrace font-bold' : 'text-(--muted) hover:text-(--ink)'"
            >
              JSON
            </button>
          </div>

          <button
            (click)="copyReportContent()"
            class="px-3.5 py-1.5 rounded bento-card-elevated hover:border-(--or) text-(--ink) text-xs font-medium border border-(--grid) transition cursor-pointer"
          >
            {{ copied() ? '✓ Copied' : '📋 Copy' }}
          </button>
          <button
            (click)="downloadReport()"
            class="btn-retrace text-xs py-1.5 px-3 flex items-center gap-2 cursor-pointer"
          >
            💾 Download
          </button>
        </div>
      </div>

      <!-- Markdown View -->
      <div *ngIf="formatMode() === 'markdown'" class="space-y-4">
        <div
          *ngFor="let sec of report?.sections || []"
          class="p-5 rounded bento-card border border-(--grid) space-y-2"
        >
          <div class="flex items-center justify-between border-b border-(--grid) pb-2">
            <h4 class="text-sm font-bold text-(--ink) uppercase">{{ sec.title }}</h4>
            <span *ngIf="sec.evidence_ids.length > 0" class="text-[11px] text-(--muted)">
              Refs: {{ sec.evidence_ids.join(', ') }}
            </span>
          </div>
          <div class="text-xs text-(--ink) whitespace-pre-wrap leading-relaxed">
            {{ sec.content_markdown }}
          </div>
        </div>
      </div>

      <!-- JSON View -->
      <div *ngIf="formatMode() === 'json'" class="p-4 rounded bento-card border border-(--grid)">
        <pre class="text-xs text-(--ink) overflow-x-auto p-3 leading-relaxed whitespace-pre bento-card-elevated rounded border border-(--grid)">{{ formattedJson }}</pre>
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
