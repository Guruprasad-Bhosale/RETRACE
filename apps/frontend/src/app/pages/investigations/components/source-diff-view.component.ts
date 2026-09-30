import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DiffHunk, RootCauseResult } from '../../../core/models/investigation.models';
import { StatusBadgeComponent } from './status-badge.component';

@Component({
  selector: 'app-source-diff-view',
  standalone: true,
  imports: [CommonModule, StatusBadgeComponent],
  template: `
    <div class="space-y-6">
      <!-- Source Attribution Header Card -->
      <div class="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <div class="flex items-center gap-3">
            <h3 class="text-base font-bold text-slate-100">Root Cause Source Attribution</h3>
            <app-status-badge [status]="rootCause?.status || 'INCONCLUSIVE'"></app-status-badge>
          </div>
          <span
            *ngIf="primaryAttribution?.relationship_type"
            class="px-2.5 py-1 rounded bg-indigo-950 text-indigo-300 text-xs font-mono font-semibold border border-indigo-800"
          >
            {{ primaryAttribution?.relationship_type }}
          </span>
        </div>

        <div *ngIf="rootCause?.status === 'CANDIDATE_ONLY'" class="p-3 rounded-lg bg-amber-950/40 border border-amber-800/60 text-xs text-amber-300">
          ⚠️ <strong>Candidate Attribution:</strong> Modified source code region identified, but empirical evidence does not conclusively establish causality.
        </div>

        <div *ngIf="rootCause?.status === 'INCONCLUSIVE'" class="p-3 rounded-lg bg-purple-950/40 border border-purple-800/60 text-xs text-purple-300">
          ℹ️ <strong>Inconclusive Attribution:</strong> Source diff analysis was inconclusive; no definitive source change could be linked to the behavioral regression.
        </div>

        <!-- Primary Localized Location Grid -->
        <div *ngIf="primaryAttribution" class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
          <div class="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <span class="text-slate-500 block text-[10px]">FILE PATH</span>
            <span class="font-bold text-slate-200 break-all">{{ primaryAttribution.source_location.file_path }}</span>
          </div>

          <div class="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <span class="text-slate-500 block text-[10px]">LINES</span>
            <span class="font-bold text-slate-200">
              {{ primaryAttribution.source_location.start_line }} – {{ primaryAttribution.source_location.end_line }}
            </span>
          </div>

          <div class="p-3 rounded-lg bg-slate-950 border border-slate-800">
            <span class="text-slate-500 block text-[10px]">AST ENCLOSING SYMBOL</span>
            <span class="font-bold text-indigo-400">
              {{ primaryAttribution.source_location.symbol_name || '(Top-Level Module)' }}
            </span>
          </div>
        </div>

        <div *ngIf="primaryAttribution?.explanation" class="text-xs text-slate-300 leading-relaxed">
          <span class="text-slate-500 font-bold block mb-1">ENGINEERING REASONING:</span>
          {{ primaryAttribution?.explanation }}
        </div>
      </div>

      <!-- Attributed Commit Card -->
      <div *ngIf="primaryAttribution?.commit" class="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
        <div class="flex items-center justify-between">
          <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Attributed Git Commit Metadata
          </h4>
          <span
            class="px-2 py-0.5 rounded text-xs font-mono font-bold"
            [ngClass]="primaryAttribution?.commit_attribution_type === 'CAUSAL_COMMIT' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-blue-950 text-blue-400 border border-blue-800'"
          >
            {{ primaryAttribution?.commit_attribution_type }}
          </span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
          <div>
            <span class="text-slate-500 block">Commit Hash:</span>
            <span class="text-slate-200 font-bold">{{ primaryAttribution?.commit?.commit_hash }}</span>
          </div>
          <div>
            <span class="text-slate-500 block">Author:</span>
            <span class="text-slate-200">{{ primaryAttribution?.commit?.author_name }} &lt;{{ primaryAttribution?.commit?.author_email }}&gt;</span>
          </div>
        </div>

        <div class="text-xs text-slate-300">
          <span class="text-slate-500 font-medium block">Commit Message:</span>
          <div class="p-2 rounded bg-slate-950 font-mono text-slate-300 mt-1 border border-slate-800">
            {{ primaryAttribution?.commit?.message }}
          </div>
        </div>
      </div>

      <!-- Normalized Git Diff Viewer -->
      <div class="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
        <div class="flex items-center justify-between">
          <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Normalized Unified Diff
          </h4>
          <span class="text-xs font-mono text-slate-500">
            Hunk Header: {{ diffHunk?.header || '@@ diff @@' }}
          </span>
        </div>

        <div *ngIf="!diffHunk || !diffHunk.lines.length" class="p-6 rounded-xl bg-slate-950 border border-slate-800 text-center text-slate-500 text-xs font-mono">
          No diff hunk lines available for this attribution.
        </div>

        <div *ngIf="diffHunk && diffHunk.lines.length" class="p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs overflow-x-auto">
          <div
            *ngFor="let line of diffHunk.lines"
            class="px-2 py-0.5 flex items-start gap-4 rounded"
            [ngClass]="getDiffLineClass(line.change_type)"
          >
            <span class="w-8 text-right text-slate-600 select-none">
              {{ line.old_line_number || '' }}
            </span>
            <span class="w-8 text-right text-slate-600 select-none">
              {{ line.new_line_number || '' }}
            </span>
            <span class="w-4 select-none font-bold">
              {{ line.change_type === 'LINE_ADDED' ? '+' : (line.change_type === 'LINE_DELETED' ? '-' : ' ') }}
            </span>
            <span class="flex-1 whitespace-pre">{{ line.content }}</span>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class SourceDiffViewComponent {
  @Input() rootCause: RootCauseResult | null = null;

  get primaryAttribution() {
    return this.rootCause?.primary_attribution || (this.rootCause?.attributions?.length ? this.rootCause.attributions[0] : null);
  }

  get diffHunk(): DiffHunk | null {
    return this.primaryAttribution?.diff_hunk || null;
  }

  getDiffLineClass(changeType: string): string {
    if (changeType === 'LINE_ADDED') {
      return 'bg-emerald-950/60 text-emerald-300 font-medium';
    }
    if (changeType === 'LINE_DELETED') {
      return 'bg-rose-950/60 text-rose-300 font-medium';
    }
    return 'text-slate-400';
  }
}
