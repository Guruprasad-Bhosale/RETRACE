import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ThemeService } from '../../core/services/theme.service';
import { ApiKeyItem } from '../../core/models';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="space-y-8 animate-reveal max-w-4xl font-mono">
      <!-- Top Title Bar -->
      <div class="border-b border-(--grid) pb-6">
        <div class="text-[10px] tracking-widest text-(--or) uppercase mb-1">
          08 / SYSTEM CONFIGURATION
        </div>
        <h1 class="text-3xl font-extrabold tracking-tight text-(--ink) flex items-center gap-3 uppercase">
          Workspace & Security Settings
        </h1>
        <p class="text-xs text-(--muted) mt-1">
          Multi-tenant workspace isolation, RBAC member roles, API key lifecycle, and appearance.
        </p>
      </div>

      <!-- Appearance / Theme Toggle -->
      <div class="bento-card p-6 space-y-4">
        <h2 class="text-sm font-bold text-(--ink) uppercase tracking-wider">
          Appearance & Contrast
        </h2>
        <div class="flex items-center justify-between pt-2">
          <div>
            <div class="text-sm font-medium text-(--ink)">Interface Theme</div>
            <div class="text-xs text-(--muted)">
              Switch between High-Contrast Obsidian Dark Command Center and Editorial Light Paper mode.
            </div>
          </div>
          <button
            (click)="themeService.toggleTheme()"
            class="px-4 py-2 rounded bento-card-elevated hover:border-(--or) text-xs font-bold text-(--ink) transition"
          >
            CURRENT: {{ themeService.currentTheme() | uppercase }}
          </button>
        </div>
      </div>

      <!-- Workspace & Tenant Isolation -->
      <div class="bento-card p-6 space-y-4">
        <h2 class="text-sm font-bold text-(--ink) uppercase tracking-wider">
          Workspace Isolation Boundary
        </h2>
        <div class="space-y-3 text-xs">
          <div class="flex justify-between p-3 rounded bento-card-elevated">
            <span class="text-(--muted)">ACTIVE WORKSPACE:</span>
            <span class="text-(--ink) font-bold">Default Engineering Laboratory (ws-00000000)</span>
          </div>
          <div class="flex justify-between p-3 rounded bento-card-elevated">
            <span class="text-(--muted)">ORGANIZATION:</span>
            <span class="text-(--ink)">RETRACE Core Organization</span>
          </div>
          <div class="flex justify-between p-3 rounded bento-card-elevated">
            <span class="text-(--muted)">YOUR ROLE:</span>
            <span class="px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800 font-bold">
              OWNER / ADMINISTRATOR
            </span>
          </div>
        </div>
      </div>

      <!-- Workspace API Keys -->
      <div class="bento-card p-6 space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-sm font-bold text-(--ink) uppercase tracking-wider">
              Workspace API Keys
            </h2>
            <p class="text-xs text-(--muted) mt-0.5">
              Secure automation tokens for CI/CD and CLI integrations. Plaintext is never stored.
            </p>
          </div>
          <button
            (click)="createKeyModal = true"
            class="btn-retrace text-xs py-1.5 px-3"
          >
            + Generate Key
          </button>
        </div>

        <div class="space-y-2 pt-2">
          @for (key of apiKeys(); track key.id) {
            <div class="p-4 rounded bento-card-elevated flex items-center justify-between text-xs">
              <div>
                <div class="font-bold text-(--ink) flex items-center gap-2">
                  <span>{{ key.name }}</span>
                  <span class="px-1.5 py-0.5 rounded bento-card text-[10px] text-(--or)">
                    {{ key.role }}
                  </span>
                </div>
                <div class="text-[11px] text-(--muted) mt-1">
                  Token Prefix: <span class="text-(--ink) font-bold">{{ key.masked_key }}</span> • Created: {{ key.created_at | date:'shortDate' }}
                </div>
              </div>
              <div class="flex items-center gap-3">
                <span class="px-2 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800">
                  ACTIVE
                </span>
              </div>
            </div>
          }
        </div>
      </div>
    </div>
  `,
})
export class SettingsComponent {
  readonly themeService = inject(ThemeService);
  createKeyModal = false;

  readonly apiKeys = signal<ApiKeyItem[]>([
    {
      id: 'key-1',
      name: 'GitHub Actions Production CI/CD',
      masked_key: 'rt_live_••••••••',
      role: 'ADMIN',
      created_at: new Date().toISOString(),
      is_active: true,
    },
    {
      id: 'key-2',
      name: 'Local Developer CLI Token',
      masked_key: 'rt_live_••••••••',
      role: 'ANALYST',
      created_at: new Date(Date.now() - 86400000 * 7).toISOString(),
      is_active: true,
    }
  ]);
}
