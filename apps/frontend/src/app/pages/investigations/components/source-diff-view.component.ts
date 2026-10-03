import { Component, Input, inject, ElementRef, ViewChild, AfterViewInit, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DiffHunk, RootCauseResult } from '../../../core/models/investigation.models';
import { StatusBadgeComponent } from './status-badge.component';
import { ForensicInteractionService } from '../../../core/services/forensic-interaction.service';

@Component({
  selector: 'app-source-diff-view',
  standalone: true,
  imports: [CommonModule, StatusBadgeComponent],
  template: `
    <div class="space-y-6 font-mono">
      <!-- 1. Progressive Root Cause Sequential Chain -->
      <div class="bento-card p-5 border border-(--grid) space-y-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-(--or) animate-pulse"></span>
            <h4 class="text-xs uppercase font-bold text-(--ink) tracking-wider">
              Forensic Root Cause Chain
            </h4>
          </div>
          <span class="text-[10px] text-(--muted)">PROGRESSIVE ATTRIBUTION</span>
        </div>

        <!-- Horizontal Chain Steps Flow -->
        <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 pt-2 text-[10px]">
          <div class="p-2 rounded bento-card-elevated border border-(--grid) text-center">
            <span class="text-[9px] text-(--muted) block">01</span>
            <strong class="text-(--ink) block truncate">USER ACTION</strong>
          </div>
          <div class="p-2 rounded bento-card-elevated border border-(--grid) text-center">
            <span class="text-[9px] text-(--muted) block">02</span>
            <strong class="text-(--ink) block truncate">OBSERVATION</strong>
          </div>
          <div class="p-2 rounded bento-card-elevated border border-(--grid) text-center">
            <span class="text-[9px] text-(--muted) block">03</span>
            <strong class="text-(--ink) block truncate">DIFFERENCE</strong>
          </div>
          <div class="p-2 rounded bento-card-elevated border border-(--grid) text-center">
            <span class="text-[9px] text-(--muted) block">04</span>
            <strong class="text-(--ink) block truncate">REPRODUCTION</strong>
          </div>
          <div class="p-2 rounded bento-card-elevated border border-(--grid) text-center">
            <span class="text-[9px] text-(--muted) block">05</span>
            <strong class="text-(--ink) block truncate">SOURCE CHANGE</strong>
          </div>
          <div class="p-2 rounded bento-card-elevated border border-(--grid) text-center">
            <span class="text-[9px] text-(--muted) block">06</span>
            <strong class="text-(--ink) block truncate">COMMIT</strong>
          </div>
          <div class="p-2 rounded bento-card-elevated border border-(--or) bg-(--surface) text-center ring-1 ring-(--or)/40">
            <span class="text-[9px] text-(--or) font-bold block">07</span>
            <strong class="text-(--or) block truncate">ROOT CAUSE</strong>
          </div>
        </div>
      </div>

      <!-- 2. Root Cause Identified Prominent Box -->
      <div
        *ngIf="rootCause"
        class="bento-card p-5 border-l-4 border-l-(--or) space-y-4 transition-all duration-300"
        [class.forensic-pulse]="primaryAttribution && forensic.selectedRootCauseAttributionId() === primaryAttribution.attribution_id"
      >
        <div class="flex items-center justify-between border-b border-(--grid) pb-3">
          <div class="flex items-center gap-3">
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 rounded bg-(--or) text-stone-900 text-xs font-bold uppercase">
                ROOT CAUSE IDENTIFIED
              </span>
              <h3 class="text-sm font-bold text-(--ink) uppercase">
                Source Attribution
              </h3>
            </div>
            <app-status-badge [status]="rootCause.status || 'INCONCLUSIVE'"></app-status-badge>
          </div>
          <span
            *ngIf="primaryAttribution?.relationship_type"
            class="px-2.5 py-1 rounded bento-card-elevated text-(--or) text-xs font-semibold border border-(--grid)"
          >
            {{ primaryAttribution.relationship_type }}
          </span>
        </div>

        <div *ngIf="rootCause.status === 'CANDIDATE_ONLY'" class="p-3 rounded bento-card-elevated border-amber-800/60 text-xs text-amber-500">
          ⚠️ <strong>Candidate Attribution:</strong> Modified source code region identified, but empirical evidence does not conclusively establish causality.
        </div>

        <div *ngIf="rootCause.status === 'INCONCLUSIVE'" class="p-3 rounded bento-card-elevated border-purple-800/60 text-xs text-purple-400">
          ℹ️ <strong>Inconclusive Attribution:</strong> Source diff analysis was inconclusive; no definitive source change could be linked to the behavioral regression.
        </div>

        <!-- Primary Localized Location Grid -->
        <div *ngIf="primaryAttribution" class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div class="p-3 rounded bento-card-elevated border border-(--grid)">
            <span class="text-(--muted) block text-[10px] uppercase">File Path</span>
            <span class="font-bold text-(--ink) break-all">{{ primaryAttribution.source_location.file_path }}</span>
          </div>

          <div class="p-3 rounded bento-card-elevated border border-(--grid)">
            <span class="text-(--muted) block text-[10px] uppercase">Lines Localized</span>
            <span class="font-bold text-(--or)">
              LINE {{ primaryAttribution.source_location.start_line }} &ndash; {{ primaryAttribution.source_location.end_line }}
            </span>
          </div>

          <div class="p-3 rounded bento-card-elevated border border-(--grid)">
            <span class="text-(--muted) block text-[10px] uppercase">AST Enclosing Symbol</span>
            <span class="font-bold text-(--ink)">
              {{ primaryAttribution.source_location.symbol_name || '(Top-Level Module)' }}
            </span>
          </div>
        </div>

        <div *ngIf="primaryAttribution?.explanation" class="text-xs text-(--ink) leading-relaxed">
          <span class="text-(--muted) font-bold block mb-1">ENGINEERING REASONING:</span>
          {{ primaryAttribution.explanation }}
        </div>
      </div>

      <!-- 3. Attributed Commit Card -->
      <div *ngIf="primaryAttribution?.commit" class="bento-card p-5 border border-(--grid) space-y-3">
        <div class="flex items-center justify-between">
          <h4 class="text-xs font-bold text-(--muted) uppercase tracking-wider">
            Attributed Git Commit Metadata
          </h4>
          <span
            class="px-2 py-0.5 rounded text-xs font-bold"
            [ngClass]="primaryAttribution.commit_attribution_type === 'CAUSAL_COMMIT' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-blue-950 text-blue-400 border border-blue-800'"
          >
            {{ primaryAttribution.commit_attribution_type }}
          </span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div>
            <span class="text-(--muted) block text-[10px] uppercase">Commit Hash:</span>
            <span class="text-(--or) font-bold font-mono">{{ primaryAttribution.commit?.commit_hash }}</span>
          </div>
          <div>
            <span class="text-(--muted) block text-[10px] uppercase">Author:</span>
            <span class="text-(--ink)">{{ primaryAttribution.commit?.author_name }} &lt;{{ primaryAttribution.commit?.author_email }}&gt;</span>
          </div>
        </div>

        <div class="text-xs text-(--ink)">
          <span class="text-(--muted) text-[10px] uppercase block">Commit Message:</span>
          <div class="p-2 rounded bento-card-elevated border border-(--grid) mt-1 font-mono text-[11px]">
            {{ primaryAttribution.commit?.message }}
          </div>
        </div>
      </div>

      <!-- 4. Normalized Git Diff & Synchronized Line Viewer -->
      <div class="bento-card p-5 border border-(--grid) space-y-3" #codeViewerContainer>
        <div class="flex items-center justify-between">
          <h4 class="text-xs font-bold text-(--muted) uppercase tracking-wider">
            Normalized Unified Diff & Source Inspector
          </h4>
          <span class="text-xs text-(--muted)">
            Hunk Header: {{ diffHunk?.header || '@@ diff @@' }}
          </span>
        </div>

        <div *ngIf="!diffHunk || !diffHunk.lines.length" class="p-6 rounded bento-card-elevated text-center text-(--muted) text-xs border border-(--grid)">
          No diff hunk lines available for this attribution.
        </div>

        <div *ngIf="diffHunk && diffHunk.lines.length" class="p-3 rounded bento-card-elevated border border-(--grid) text-xs overflow-x-auto code-container">
          <div
            *ngFor="let line of diffHunk.lines"
            (click)="onLineClick(line.new_line_number || line.old_line_number || 1)"
            tabindex="0"
            role="row"
            class="px-2 py-1 flex items-start gap-4 rounded cursor-pointer transition-colors"
            [ngClass]="getDiffLineClass(line.change_type, line.new_line_number || line.old_line_number)"
          >
            <span class="w-8 text-right text-(--muted) select-none">
              {{ line.old_line_number || '' }}
            </span>
            <span class="w-8 text-right text-(--muted) select-none">
              {{ line.new_line_number || '' }}
            </span>
            <span class="w-4 select-none font-bold">
              {{ line.change_type === 'LINE_ADDED' ? '+' : (line.change_type === 'LINE_DELETED' ? '-' : ' ') }}
            </span>
            <span class="flex-1 whitespace-pre font-mono">{{ line.content }}</span>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class SourceDiffViewComponent implements AfterViewInit {
  @Input() rootCause: RootCauseResult | null = null;
  @ViewChild('codeViewerContainer') codeViewerContainer?: ElementRef;

  readonly forensic = inject(ForensicInteractionService);

  get primaryAttribution() {
    return this.rootCause?.primary_attribution || (this.rootCause?.attributions?.length ? this.rootCause.attributions[0] : null);
  }

  get diffHunk(): DiffHunk | null {
    return this.primaryAttribution?.diff_hunk || null;
  }

  ngAfterViewInit(): void {
    // Check if line should be scrolled into view
    const targetLine = this.forensic.highlightedSourceLine();
    if (targetLine && this.codeViewerContainer) {
      this.codeViewerContainer.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  onLineClick(lineNumber: number): void {
    const file = this.primaryAttribution?.source_location?.file_path;
    this.forensic.selectSourceLine(lineNumber, file);
  }

  getDiffLineClass(changeType: string, lineNumber?: number | null): string {
    const isTargetLine = lineNumber !== null && lineNumber !== undefined && this.forensic.highlightedSourceLine() === lineNumber;
    let base = '';

    if (changeType === 'LINE_ADDED') {
      base = 'bg-emerald-950/60 text-emerald-300 font-medium';
    } else if (changeType === 'LINE_DELETED') {
      base = 'bg-rose-950/60 text-rose-300 font-medium';
    } else {
      base = 'text-[#E7E4DB] hover:bg-stone-800/40';
    }

    if (isTargetLine) {
      base += ' code-line-highlight sweep-highlight';
    }

    return base;
  }
}
