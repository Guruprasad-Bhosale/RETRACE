import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Project } from '../../core/models';

@Component({
  selector: 'app-projects',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="space-y-8 animate-reveal">
      <!-- Top Title Bar -->
      <div class="flex flex-wrap items-center justify-between gap-4 border-b border-(--grid) pb-6">
        <div>
          <div class="text-[10px] font-mono tracking-widest text-(--or) uppercase mb-1">
            02 / EXPERIMENTAL TARGETS
          </div>
          <h1 class="text-3xl font-extrabold tracking-tight text-(--ink) flex items-center gap-3 uppercase">
            Investigation Laboratories & Repositories
          </h1>
          <p class="text-xs font-mono text-(--muted) mt-1">
            Isolated Version A (Baseline) and Version B (Target Release) evaluation testbeds.
          </p>
        </div>
      </div>

      <!-- Projects Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 font-mono">
        @for (project of projects(); track project.id) {
          <div class="bento-card p-6 space-y-5 group">
            <div class="flex items-center justify-between">
              <span class="text-[10px] text-(--or) font-bold uppercase tracking-wider">LAB #01</span>
              <span class="px-2 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800">
                ACTIVE LAB
              </span>
            </div>

            <div>
              <h2 class="text-xl font-bold text-(--ink) group-hover:text-(--or) transition">
                {{ project.name }}
              </h2>
              <p class="text-xs text-(--muted) mt-1.5 leading-relaxed">
                {{ project.description || 'Isolated two-version e-commerce web application with seeded defect taxonomy.' }}
              </p>
            </div>

            <!-- Version A vs Version B Endpoint Mapping -->
            <div class="space-y-2 pt-2 border-t border-(--grid) text-xs">
              <div class="flex items-center justify-between p-2.5 bento-card-elevated">
                <span class="text-(--muted)">VERSION A (BASELINE):</span>
                <span class="text-(--ink) font-bold">{{ project.version_a_url || 'http://localhost:3001' }}</span>
              </div>
              <div class="flex items-center justify-between p-2.5 bento-card-elevated">
                <span class="text-(--muted)">VERSION B (TARGET):</span>
                <span class="text-(--ink) font-bold">{{ project.version_b_url || 'http://localhost:3002' }}</span>
              </div>
            </div>

            <!-- Action Trigger -->
            <div class="pt-2 flex items-center justify-between">
              <span class="text-[11px] text-(--muted)">6 Seeded Regressions • 3 Non-Regressions</span>
              <a
                routerLink="/analyses"
                class="inline-flex items-center gap-1.5 text-xs text-(--or) font-bold hover:underline"
              >
                Inspect Runs →
              </a>
            </div>
          </div>
        } @empty {
          <div class="col-span-2 p-12 text-center bento-card text-xs text-(--muted) font-mono">
            No projects registered.
          </div>
        }
      </div>
    </div>
  `,
})
export class ProjectsComponent implements OnInit {
  private readonly api = inject(ApiService);
  readonly projects = signal<Project[]>([]);

  ngOnInit(): void {
    this.api.getProjects().subscribe((data) => this.projects.set(data));
  }
}
