import { Component, OnInit, OnDestroy, inject, signal, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, NavigationEnd, RouterLink, RouterOutlet } from '@angular/router';
import { filter, Subscription } from 'rxjs';
import { ApiService } from './core/services/api.service';
import { ThemeService } from './core/services/theme.service';

export interface NavRailItem {
  number: string;
  title: string;
  subtitle: string;
  route: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit, OnDestroy {
  readonly platformName = 'RETRACE';
  readonly api = inject(ApiService);
  readonly themeService = inject(ThemeService);
  private readonly router = inject(Router);

  readonly status = this.api.systemStatus;
  readonly mobileMenuOpen = signal<boolean>(false);
  readonly activeNavIndex = signal<number>(0);
  readonly isCurrentRouteInvestigation = signal<boolean>(false);
  readonly isLandingPage = signal<boolean>(false);

  readonly navItems: NavRailItem[] = [
    { number: '01', title: 'OVERVIEW', subtitle: 'Command center & hero', route: '/dashboard' },
    { number: '02', title: 'PROJECTS', subtitle: 'Target laboratories', route: '/projects' },
    { number: '03', title: 'ANALYSES', subtitle: 'State machine runs', route: '/analyses' },
    { number: '04', title: 'INVESTIGATIONS', subtitle: 'Case files & findings', route: '/investigations' },
    { number: '05', title: 'EVIDENCE', subtitle: 'Evidence graph & DAG', route: '/investigations' },
    { number: '06', title: 'OBSERVABILITY', subtitle: 'Telemetry & streams', route: '/observability' },
    { number: '07', title: 'OPERATIONS', subtitle: 'Subsystem topology', route: '/operations' },
    { number: '08', title: 'SETTINGS', subtitle: 'Workspaces & security', route: '/settings' },
  ];

  private routerSub?: Subscription;

  ngOnInit(): void {
    this.api.getSystemStatus().subscribe();
    this.updateActiveIndexFromUrl(this.router.url);

    this.routerSub = this.router.events
      .pipe(filter((event): event is NavigationEnd => event instanceof NavigationEnd))
      .subscribe((event) => {
        this.updateActiveIndexFromUrl(event.urlAfterRedirects || event.url);
        this.mobileMenuOpen.set(false);
      });
  }

  ngOnDestroy(): void {
    this.routerSub?.unsubscribe();
  }

  toggleMobileMenu(): void {
    this.mobileMenuOpen.update((v) => !v);
  }

  closeMobileMenu(index?: number): void {
    this.mobileMenuOpen.set(false);
    if (index !== undefined) {
      this.activeNavIndex.set(index);
    }
  }

  setActiveIndex(index: number): void {
    this.activeNavIndex.set(index);
  }

  private updateActiveIndexFromUrl(url: string): void {
    const cleanUrl = url.split('?')[0].split('#')[0];
    const isLanding = cleanUrl === '/' || cleanUrl === '';
    this.isLandingPage.set(isLanding);
    this.isCurrentRouteInvestigation.set(cleanUrl.includes('/investigations'));

    if (cleanUrl.includes('/projects')) {
      this.activeNavIndex.set(1);
    } else if (cleanUrl.includes('/analyses')) {
      this.activeNavIndex.set(2);
    } else if (cleanUrl.includes('/investigations')) {
      this.activeNavIndex.set(3);
    } else if (cleanUrl.includes('/observability')) {
      this.activeNavIndex.set(5);
    } else if (cleanUrl.includes('/operations')) {
      this.activeNavIndex.set(6);
    } else if (cleanUrl.includes('/settings')) {
      this.activeNavIndex.set(7);
    } else {
      this.activeNavIndex.set(0);
    }
  }

  @HostListener('window:mousemove', ['$event'])
  onMouseMove(e: MouseEvent): void {
    if (typeof window !== 'undefined' && typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return;
    }
    const glow = document.getElementById('glow');
    if (!glow) return;

    const target = e.target as HTMLElement | null;

    // Contextual cursor behaviors (Section 16)
    // 1. Code viewer -> disable glow completely
    if (target?.closest('.code-container, pre, code')) {
      glow.style.opacity = '0';
      return;
    }

    // 2. Evidence node -> smaller focused glow
    const isEvidenceNode = target?.closest('[role="button"], .bento-card-elevated');
    if (isEvidenceNode) {
      glow.style.transform = `translate(${e.clientX}px, ${e.clientY}px) scale(0.6)`;
      glow.style.opacity = '0.22';
      return;
    }

    // 3. Button / Interactive link -> slightly larger glow
    const isInteractive = target?.closest('a, button, .btn-retrace, input');
    if (isInteractive) {
      glow.style.transform = `translate(${e.clientX}px, ${e.clientY}px) scale(1.35)`;
      glow.style.opacity = '0.18';
      return;
    }

    // Default ambient glow
    glow.style.transform = `translate(${e.clientX}px, ${e.clientY}px) scale(0.85)`;
    glow.style.opacity = '0.07';
  }

  @HostListener('window:keydown', ['$event'])
  onKeyDown(e: KeyboardEvent): void {
    if (e.key === 'Escape' && this.mobileMenuOpen()) {
      this.mobileMenuOpen.set(false);
    }
  }
}
