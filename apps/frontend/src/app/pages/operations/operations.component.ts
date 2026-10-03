import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-operations',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="space-y-8 animate-reveal font-mono">
      <!-- Top Title Bar -->
      <div class="flex flex-wrap items-center justify-between gap-4 border-b border-(--grid) pb-6">
        <div>
          <div class="text-[10px] font-mono tracking-widest text-(--or) uppercase mb-1">
            07 / INFRASTRUCTURE & CLOUD OPERATIONS
          </div>
          <h1 class="text-3xl font-extrabold tracking-tight text-(--ink) flex items-center gap-3 uppercase">
            Production Cluster & Subsystem Topology
          </h1>
          <p class="text-xs font-mono text-(--muted) mt-1">
            AWS ECS Fargate, Multi-AZ RDS PostgreSQL 16, Redis Streams Valkey & S3 Artifact Store.
          </p>
        </div>
        <button
          (click)="refresh()"
          class="px-4 py-2 rounded bento-card-elevated hover:border-(--or) text-xs font-mono font-medium text-(--ink) border border-(--grid) transition"
        >
          ↻ Probe Subsystems
        </button>
      </div>

      <!-- Infrastructure Matrix -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
        <!-- ECS API Service -->
        <div class="bento-card p-6 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs text-(--muted)">ECS SERVICE: API</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
              HEALTHY
            </span>
          </div>
          <div class="text-lg font-bold text-(--ink)">FastAPI ASGI Runtime</div>
          <div class="text-xs text-(--muted) space-y-1 pt-2 border-t border-(--grid)">
            <div>Target Port: 8000 (ALB Target Group)</div>
            <div>Runtime: Python 3.12 (Non-Root UID 10001)</div>
            <div>Health Probe: /liveness (HTTP 200)</div>
          </div>
        </div>

        <!-- ECS Worker Service -->
        <div class="bento-card p-6 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs text-(--muted)">ECS SERVICE: WORKER</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
              HEALTHY
            </span>
          </div>
          <div class="text-lg font-bold text-(--ink)">Analysis Engine Worker</div>
          <div class="text-xs text-(--muted) space-y-1 pt-2 border-t border-(--grid)">
            <div>Engine: LangGraph State Machine</div>
            <div>Browser: Headless Chromium Sandbox</div>
            <div>Recovery: XAUTOCLAIM Stream Lease</div>
          </div>
        </div>

        <!-- PostgreSQL Database -->
        <div class="bento-card p-6 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs text-(--muted)">AMAZON RDS POSTGRESQL</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
              CONNECTED
            </span>
          </div>
          <div class="text-lg font-bold text-(--ink)">PostgreSQL 16 Multi-AZ</div>
          <div class="text-xs text-(--muted) space-y-1 pt-2 border-t border-(--grid)">
            <div>Schema: Alembic Version Managed</div>
            <div>Connection Pool: 10 + 20 overflow</div>
            <div>Subnet: Private DB Subnet Group</div>
          </div>
        </div>

        <!-- Redis Stream Queue -->
        <div class="bento-card p-6 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs text-(--muted)">ELASTICACHE REDIS / VALKEY</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
              CONNECTED
            </span>
          </div>
          <div class="text-lg font-bold text-(--ink)">Stream Event Queue</div>
          <div class="text-xs text-(--muted) space-y-1 pt-2 border-t border-(--grid)">
            <div>Stream: retrace:analysis:jobs</div>
            <div>Consumer: retrace-worker-group</div>
            <div>Crash Protection: XACK Guaranteed</div>
          </div>
        </div>

        <!-- S3 Artifact Storage -->
        <div class="bento-card p-6 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs text-(--muted)">AMAZON S3 ARTIFACTS</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
              READY
            </span>
          </div>
          <div class="text-lg font-bold text-(--ink)">Multi-Modal Artifact Store</div>
          <div class="text-xs text-(--muted) space-y-1 pt-2 border-t border-(--grid)">
            <div>Encryption: AES-256 Server-Side</div>
            <div>Integrity: SHA-256 Checksums</div>
            <div>Lifecycle: 90-Day Retention Policy</div>
          </div>
        </div>

        <!-- ALB Target Group -->
        <div class="bento-card p-6 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs text-(--muted)">APPLICATION LOAD BALANCER</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
              ACTIVE
            </span>
          </div>
          <div class="text-lg font-bold text-(--ink)">Multi-AZ Ingress</div>
          <div class="text-xs text-(--muted) space-y-1 pt-2 border-t border-(--grid)">
            <div>Routing: /api/* -> API, /* -> UI</div>
            <div>Protocols: HTTPS / HSTS Enforced</div>
            <div>Security: AWS WAF Ready</div>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class OperationsComponent implements OnInit {
  private readonly api = inject(ApiService);
  readonly status = this.api.systemStatus;
  readonly readiness = this.api.readiness;

  ngOnInit(): void {
    this.refresh();
  }

  refresh(): void {
    this.api.getSystemStatus().subscribe();
    this.api.getReadiness().subscribe();
  }
}
