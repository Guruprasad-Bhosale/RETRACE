import { Component, Input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { GeneratedTest } from '../../../core/models/investigation.models';
import { StatusBadgeComponent } from './status-badge.component';

@Component({
  selector: 'app-generated-test-view',
  standalone: true,
  imports: [CommonModule, StatusBadgeComponent],
  styles: [':host { display: block; }'],
  template: `

    <div class="space-y-6 font-mono">

      <!-- Derived Artifact Notice Banner -->
      <div class="p-3.5 rounded bento-card border border-indigo-900/60 bg-indigo-950/20 flex items-center justify-between text-xs text-indigo-300">
        <div class="flex items-center gap-2">
          <span class="font-bold px-2 py-0.5 rounded bento-card-elevated text-indigo-400 border border-indigo-700">DERIVED TEST ARTIFACT</span>
          <span>Synthesized deterministically from verified Phase 8 reproduction path and Phase 6-8 evidence.</span>
        </div>
      </div>

      <!-- Test Header Card -->
      <div class="p-5 rounded bento-card border border-(--grid) flex flex-wrap items-center justify-between gap-4">
        <div class="space-y-1">
          <div class="flex items-center gap-3">
            <h3 class="text-base font-bold text-(--ink) uppercase">{{ generatedTest?.title || 'Regression Test' }}</h3>
            <app-status-badge [status]="generatedTest?.validation_status || 'NOT_VALIDATED'"></app-status-badge>
          </div>
          <p class="text-xs text-(--muted)">
            {{ generatedTest?.description || 'Playwright test script reproducing regression.' }}
          </p>
        </div>

        <!-- Actions: Copy / Download -->
        <div class="flex items-center gap-2">
          <button
            (click)="copyTestCode()"
            class="px-3.5 py-1.5 rounded bento-card-elevated hover:border-(--or) text-(--ink) text-xs font-medium border border-(--grid) transition flex items-center gap-2 cursor-pointer"
          >
            <span>{{ copied() ? '✓ Copied' : '📋 Copy Spec' }}</span>
          </button>
          <button
            (click)="downloadTestFile()"
            class="btn-retrace text-xs py-1.5 px-3 flex items-center gap-2"
          >
            <span>💾 Download .spec.ts</span>
          </button>
        </div>
      </div>

      <!-- Test Metadata Metrics -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
        <div class="p-4 rounded bento-card border border-(--grid)">
          <span class="text-(--muted) block text-[10px] uppercase font-bold">FRAMEWORK</span>
          <span class="font-bold text-(--ink) block mt-1">{{ generatedTest?.framework || 'PLAYWRIGHT' }} ({{ generatedTest?.language || 'TYPESCRIPT' }})</span>
        </div>
        <div class="p-4 rounded bento-card border border-(--grid)">
          <span class="text-(--muted) block text-[10px] uppercase font-bold">ACTION STEPS</span>
          <span class="font-bold text-(--ink) block mt-1">{{ generatedTest?.steps?.length || 0 }}</span>
        </div>
        <div class="p-4 rounded bento-card border border-(--grid)">
          <span class="text-(--muted) block text-[10px] uppercase font-bold">EVIDENCE ASSERTIONS</span>
          <span class="font-bold text-(--ink) block mt-1">{{ generatedTest?.assertions?.length || 0 }}</span>
        </div>
        <div class="p-4 rounded bento-card border border-(--grid)">
          <span class="text-(--muted) block text-[10px] uppercase font-bold">TARGET MODE</span>
          <span class="font-bold text-(--or) block mt-1">{{ generatedTest?.target_version || 'A_B_DUAL' }}</span>
        </div>
      </div>

      <!-- Validation Notes -->
      <div *ngIf="generatedTest?.validation_notes?.length" class="p-4 rounded bento-card border border-(--grid) text-xs text-(--muted) space-y-1">
        <span class="text-(--muted) font-bold block text-[10px] uppercase">Static Validation Verification:</span>
        <ul class="list-disc list-inside space-y-0.5 text-[11px] text-(--ink)">
          <li *ngFor="let note of generatedTest?.validation_notes">{{ note }}</li>
        </ul>
      </div>

      <!-- Test Source Code Viewer -->
      <div class="p-4 rounded bento-card border border-(--grid) space-y-2">
        <div class="flex items-center justify-between text-xs text-(--muted) pb-2 border-b border-(--grid)">
          <span>{{ generatedTest?.test_id ? generatedTest!.test_id + '.spec.ts' : 'regression.spec.ts' }}</span>
          <span>TypeScript (Playwright Test)</span>
        </div>
        <pre class="text-xs text-(--ink) overflow-x-auto p-3 leading-relaxed whitespace-pre bento-card-elevated rounded border border-(--grid)">{{ generatedTest?.generated_source || '// Test source code not available' }}</pre>
      </div>
    </div>
  `,
})
export class GeneratedTestViewComponent {

  @Input() generatedTest: GeneratedTest | null = null;
  readonly copied = signal<boolean>(false);

  copyTestCode(): void {
    if (!this.generatedTest?.generated_source) return;
    navigator.clipboard.writeText(this.generatedTest.generated_source);
    this.copied.set(true);
    setTimeout(() => this.copied.set(false), 2000);
  }

  downloadTestFile(): void {
    if (!this.generatedTest?.generated_source) return;
    const blob = new Blob([this.generatedTest.generated_source], { type: 'text/typescript' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${this.generatedTest.test_id || 'regression'}.spec.ts`;
    a.click();
    window.URL.revokeObjectURL(url);
  }
}
