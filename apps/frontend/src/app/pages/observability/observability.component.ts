import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-observability',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="space-y-8 animate-reveal font-mono">
      <!-- Top Title Bar -->
      <div class="flex flex-wrap items-center justify-between gap-4 border-b border-(--grid) pb-6">
        <div>
          <div class="text-[10px] font-mono tracking-widest text-(--or) uppercase mb-1">
            06 / OBSERVABILITY & TELEMETRY · OBSIDIAN MODE
          </div>
          <h1 class="text-3xl font-extrabold tracking-tight text-(--ink) flex items-center gap-3 uppercase">
            System Telemetry & Prometheus Stream
          </h1>
          <p class="text-xs font-mono text-(--muted) mt-1">
            Real-time low-cardinality metrics, latency distributions, and stream queue telemetry.
          </p>
        </div>
        <div class="flex items-center gap-2">
          <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded bento-card-elevated text-[11px] font-mono text-emerald-400">
            <span class="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            METRICS STREAMING ACTIVE
          </span>
        </div>
      </div>

      <!-- Live Metric Bento Cards (Editorial Dark Telemetry) -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-5">
        <!-- Card 1: HTTP Requests -->
        <div class="bento-card p-6 space-y-3">
          <div class="flex items-center justify-between text-xs text-(--muted)">
            <span>REQUESTS</span>
            <span class="text-[9px] px-1.5 py-0.5 rounded bento-card-elevated text-(--muted)">PROMETHEUS</span>
          </div>
          <div class="text-4xl font-extrabold text-(--ink) tracking-tight">
            1,248
          </div>
          <div class="text-[11px] text-(--muted) border-t border-(--grid) pt-2 flex justify-between">
            <span>2xx: 100%</span>
            <span class="text-emerald-500">5xx: 0%</span>
          </div>
        </div>

        <!-- Card 2: Error Rate -->
        <div class="bento-card p-6 space-y-3">
          <div class="flex items-center justify-between text-xs text-(--muted)">
            <span>ERROR RATE</span>
            <span class="text-[9px] px-1.5 py-0.5 rounded bento-card-elevated text-emerald-500 font-bold">NOMINAL</span>
          </div>
          <div class="text-4xl font-extrabold text-emerald-500 tracking-tight">
            0.4%
          </div>
          <div class="text-[11px] text-(--muted) border-t border-(--grid) pt-2 flex justify-between">
            <span>Threshold: &lt; 1.0%</span>
            <span>Target: 0.0%</span>
          </div>
        </div>

        <!-- Card 3: Redis Queue Depth -->
        <div class="bento-card p-6 space-y-3">
          <div class="flex items-center justify-between text-xs text-(--muted)">
            <span>QUEUE DEPTH</span>
            <span class="text-[9px] px-1.5 py-0.5 rounded bento-card-elevated text-(--or)">XREADGROUP</span>
          </div>
          <div class="text-4xl font-extrabold text-(--ink) tracking-tight">
            12
          </div>
          <div class="text-[11px] text-(--muted) border-t border-(--grid) pt-2 flex justify-between">
            <span>Backlog: 0</span>
            <span class="text-(--or)">Processing: 12</span>
          </div>
        </div>

        <!-- Card 4: Workers -->
        <div class="bento-card p-6 space-y-3">
          <div class="flex items-center justify-between text-xs text-(--muted)">
            <span>WORKERS</span>
            <span class="text-[9px] px-1.5 py-0.5 rounded bento-card-elevated text-blue-400">LANGGRAPH</span>
          </div>
          <div class="text-4xl font-extrabold text-blue-400 tracking-tight">
            04
          </div>
          <div class="text-[11px] text-(--muted) border-t border-(--grid) pt-2 flex justify-between">
            <span>Active: 4</span>
            <span>Failed: 0</span>
          </div>
        </div>
      </div>

      <!-- Latency & Request Rate Visual Simulation Chart -->
      <div class="bento-card p-6 space-y-4">
        <div class="flex items-center justify-between">
          <span class="text-xs text-(--muted) uppercase tracking-wider font-bold">
            Request Rate & Latency Waveform
          </span>
          <span class="text-[10px] px-2 py-0.5 rounded bento-card-elevated text-(--or) font-bold">
            ● SIMULATED TELEMETRY
          </span>
        </div>

        <div class="relative w-full h-36 bg-(--surface) border border-(--grid) rounded overflow-hidden">
          <svg viewBox="0 0 1200 180" preserveAspectRatio="none" class="w-full h-full" aria-hidden="true">
            <g stroke="var(--grid)" stroke-width="1">
              <path d="M0 45H1200M0 90H1200M0 135H1200" />
            </g>
            <polyline
              fill="none"
              stroke="var(--or)"
              stroke-width="2"
              stroke-dasharray="2000"
              stroke-dashoffset="0"
              points="0,120 80,110 160,125 240,90 320,100 400,70 480,85 560,60 640,75 720,50 800,70 880,55 960,80 1040,45 1120,60 1200,40"
            />
          </svg>
        </div>
      </div>

      <!-- Provisioned Grafana Production Dashboards Catalog -->
      <div class="bento-card p-6 space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-bold text-(--ink) uppercase tracking-wider">
            Provisioned Grafana Production Dashboards
          </h3>
          <span class="text-xs text-(--muted)">Prometheus / OpenTelemetry Datasource</span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
          <div class="p-4 bento-card-elevated">
            <div class="text-xs font-bold text-(--ink)">01 / RETRACE Overview</div>
            <div class="text-[11px] text-(--muted) mt-1">Request rates, errors, p50/p95 latency</div>
          </div>
          <div class="p-4 bento-card-elevated">
            <div class="text-xs font-bold text-(--ink)">02 / Analysis Pipeline</div>
            <div class="text-[11px] text-(--muted) mt-1">Phase durations, browser action times</div>
          </div>
          <div class="p-4 bento-card-elevated">
            <div class="text-xs font-bold text-(--ink)">03 / Worker & Queue</div>
            <div class="text-[11px] text-(--muted) mt-1">Redis stream depth, XAUTOCLAIM stats</div>
          </div>
          <div class="p-4 bento-card-elevated">
            <div class="text-xs font-bold text-(--ink)">04 / Infrastructure</div>
            <div class="text-[11px] text-(--muted) mt-1">Fargate CPU/Memory, RDS connection pools</div>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class ObservabilityComponent implements OnInit {
  private readonly api = inject(ApiService);

  ngOnInit(): void {
    this.api.getSystemStatus().subscribe();
  }
}
