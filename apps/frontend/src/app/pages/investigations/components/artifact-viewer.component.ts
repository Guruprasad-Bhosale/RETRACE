import { Component, Input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ArtifactReference } from '../../../core/models/investigation.models';

@Component({
  selector: 'app-artifact-viewer',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-base font-semibold text-slate-100 flex items-center gap-2">
            <span class="text-indigo-400 font-mono">📦</span>
            Multi-Modal Investigation Artifacts
          </h3>
          <p class="text-xs text-slate-400 mt-0.5">
            Immutable persisted artifacts supporting the causal investigation package.
          </p>
        </div>
        <span class="text-xs font-mono text-slate-500">
          {{ artifacts.length }} Artifacts Attached
        </span>
      </div>

      <div *ngIf="artifacts.length === 0" class="p-8 rounded-xl bg-slate-900/40 border border-slate-800 text-center text-slate-500 text-xs font-mono">
        No artifacts directly attached to this investigation package.
      </div>

      <!-- Artifacts Table / Grid -->
      <div *ngIf="artifacts.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          *ngFor="let art of artifacts"
          class="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 flex flex-col justify-between space-y-3 transition"
        >
          <div>
            <div class="flex items-center justify-between">
              <span
                class="px-2 py-0.5 rounded text-[11px] font-mono font-bold uppercase"
                [ngClass]="getKindBadgeClass(art.kind)"
              >
                {{ art.kind }}
              </span>
              <span class="text-[11px] font-mono text-slate-500">
                {{ formatBytes(art.size_bytes) }}
              </span>
            </div>

            <div class="mt-2.5">
              <span class="text-xs font-mono font-bold text-slate-200 break-all">
                {{ art.storage_uri }}
              </span>
              <span class="text-[11px] text-slate-500 block mt-0.5">
                MIME: {{ art.mime_type }}
              </span>
            </div>
          </div>

          <div class="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <span *ngIf="art.sha256_hash" class="font-mono text-[10px] text-slate-500 truncate max-w-[180px]">
              SHA: {{ art.sha256_hash }}
            </span>
            <span *ngIf="!art.sha256_hash" class="text-[10px] text-slate-600 font-mono">
              (No SHA hash)
            </span>

            <button
              *ngIf="isScreenshot(art)"
              (click)="previewScreenshot.set(art)"
              class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-mono transition"
            >
              👁 View Image
            </button>
          </div>
        </div>
      </div>

      <!-- Screenshot Preview Modal -->
      <div
        *ngIf="previewScreenshot()"
        class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
      >
        <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full p-5 space-y-4 shadow-2xl">
          <div class="flex items-center justify-between border-b border-slate-800 pb-3">
            <h4 class="text-sm font-bold text-slate-100 font-mono">
              Screenshot Preview: {{ previewScreenshot()?.storage_uri }}
            </h4>
            <button
              (click)="previewScreenshot.set(null)"
              class="text-xs text-slate-400 hover:text-slate-200 font-mono"
            >
              ✕ Close
            </button>
          </div>

          <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-center min-h-[300px]">
            <div class="text-center text-xs font-mono text-slate-400 space-y-2">
              <span class="text-3xl block">🖼️</span>
              <span>Artifact URI: {{ previewScreenshot()?.storage_uri }}</span>
              <span class="block text-slate-500 text-[10px]">Secure preview placeholder (Sandbox Isolation Active)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class ArtifactViewerComponent {
  @Input() artifacts: ArtifactReference[] = [];
  readonly previewScreenshot = signal<ArtifactReference | null>(null);

  isScreenshot(art: ArtifactReference): boolean {
    return (
      art.kind.toLowerCase().includes('screenshot') ||
      art.mime_type.toLowerCase().includes('image')
    );
  }

  getKindBadgeClass(kind: string): string {
    const k = kind.toLowerCase();
    if (k.includes('screenshot')) return 'bg-purple-950 text-purple-300 border border-purple-800';
    if (k.includes('test')) return 'bg-emerald-950 text-emerald-300 border border-emerald-800';
    if (k.includes('trace') || k.includes('har')) return 'bg-blue-950 text-blue-300 border border-blue-800';
    if (k.includes('dom')) return 'bg-amber-950 text-amber-300 border border-amber-800';
    return 'bg-slate-950 text-slate-300 border border-slate-800';
  }

  formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}
