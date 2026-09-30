import { Component, Input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { GeneratedTest } from '../../../core/models/investigation.models';
import { StatusBadgeComponent } from './status-badge.component';

@Component({
  selector: 'app-generated-test-view',
  standalone: true,
  imports: [CommonModule, StatusBadgeComponent],
  template: `
    <div class="space-y-6">
      <!-- Derived Artifact Notice Banner -->
      <div class="p-3.5 rounded-xl bg-indigo-950/40 border border-indigo-800/60 flex items-center justify-between text-xs text-indigo-300">
        <div class="flex items-center gap-2">
          <span class="font-mono font-bold px-2 py-0.5 rounded bg-indigo-900/60 border border-indigo-700">DERIVED TEST ARTIFACT</span>
          <span>Synthesized deterministically from verified Phase 8 reproduction path and Phase 6-8 evidence.</span>
        </div>
      </div>

      <!-- Test Header Card -->
      <div class="p-5 rounded-xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div class="space-y-1">
          <div class="flex items-center gap-3">
            <h3 class="text-base font-bold text-slate-100">{{ generatedTest?.title || 'Regression Test' }}</h3>
            <app-status-badge [status]="generatedTest?.validation_status || 'NOT_VALIDATED'"></app-status-badge>
          </div>
          <p class="text-xs text-slate-400">
            {{ generatedTest?.description || 'Playwright test script reproducing regression.' }}
          </p>
        </div>

        <!-- Actions: Copy / Download -->
        <div class="flex items-center gap-3">
          <button
            (click)="copyTestCode()"
            class="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-medium border border-slate-700 transition flex items-center gap-2"
          >
            <span>{{ copied() ? '✓ Copied' : '📋 Copy Spec' }}</span>
          </button>
          <button
            (click)="downloadTestFile()"
            class="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-mono font-medium shadow-md shadow-indigo-600/20 transition flex items-center gap-2"
          >
            <span>💾 Download .spec.ts</span>
          </button>
        </div>
      </div>

      <!-- Test Metadata Metrics -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
        <div class="p-3 rounded-lg bg-slate-900 border border-slate-800">
          <span class="text-slate-500 block text-[10px]">FRAMEWORK</span>
          <span class="font-bold text-slate-200">{{ generatedTest?.framework || 'PLAYWRIGHT' }} ({{ generatedTest?.language || 'TYPESCRIPT' }})</span>
        </div>
        <div class="p-3 rounded-lg bg-slate-900 border border-slate-800">
          <span class="text-slate-500 block text-[10px]">ACTION STEPS</span>
          <span class="font-bold text-slate-200">{{ generatedTest?.steps?.length || 0 }}</span>
        </div>
        <div class="p-3 rounded-lg bg-slate-900 border border-slate-800">
          <span class="text-slate-500 block text-[10px]">EVIDENCE ASSERTIONS</span>
          <span class="font-bold text-slate-200">{{ generatedTest?.assertions?.length || 0 }}</span>
        </div>
        <div class="p-3 rounded-lg bg-slate-900 border border-slate-800">
          <span class="text-slate-500 block text-[10px]">TARGET MODE</span>
          <span class="font-bold text-indigo-400">{{ generatedTest?.target_version || 'A_B_DUAL' }}</span>
        </div>
      </div>

      <!-- Validation Notes -->
      <div *ngIf="generatedTest?.validation_notes?.length" class="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400 space-y-1">
        <span class="text-slate-500 font-bold block text-[10px] uppercase font-mono">Static Validation Verification:</span>
        <ul class="list-disc list-inside space-y-0.5 font-mono text-[11px] text-slate-300">
          <li *ngFor="let note of generatedTest?.validation_notes">{{ note }}</li>
        </ul>
      </div>

      <!-- Test Source Code Viewer -->
      <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
        <div class="flex items-center justify-between text-xs text-slate-500 font-mono pb-2 border-b border-slate-800">
          <span>{{ generatedTest?.test_id ? generatedTest!.test_id + '.spec.ts' : 'regression.spec.ts' }}</span>
          <span>TypeScript (Playwright Test)</span>
        </div>
        <pre class="font-mono text-xs text-slate-300 overflow-x-auto p-2 leading-relaxed whitespace-pre">{{ generatedTest?.generated_source || '// Test source code not available' }}</pre>
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
