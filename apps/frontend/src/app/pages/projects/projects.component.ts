import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';
import { Project } from '../../core/models';

@Component({
  selector: 'app-projects',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="space-y-6">
      <div class="flex items-center justify-between border-b border-slate-800 pb-5">
        <div>
          <h1 class="text-2xl font-bold tracking-tight text-white">Investigation Projects</h1>
          <p class="text-sm text-slate-400 mt-1">Manage target applications, repositories, and benchmark baselines</p>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        @for (project of projects(); track project.id) {
          <div class="p-5 rounded-xl bg-slate-900 border border-slate-800">
            <h3 class="text-base font-semibold text-slate-100">{{ project.name }}</h3>
            <p class="text-xs text-slate-400 mt-1">{{ project.description || 'No description provided.' }}</p>
            <div class="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
              <span>ID: {{ project.id }}</span>
              <span>Active</span>
            </div>
          </div>
        } @empty {
          <div class="col-span-2 p-8 text-center rounded-xl bg-slate-900 border border-slate-800 text-slate-400 text-sm">
            No projects found.
          </div>
        }
      </div>
    </div>
  `
})
export class ProjectsComponent implements OnInit {
  private readonly api = inject(ApiService);
  readonly projects = signal<Project[]>([]);

  ngOnInit(): void {
    this.api.getProjects().subscribe((data) => this.projects.set(data));
  }
}
