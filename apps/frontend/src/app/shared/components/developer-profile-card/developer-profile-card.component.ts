import {
  Component,
  ElementRef,
  HostListener,
  Input,
  OnDestroy,
  OnInit,
  ViewChild,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-developer-profile-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './developer-profile-card.component.html',
  styleUrl: './developer-profile-card.component.css',
})
export class DeveloperProfileCardComponent implements OnInit, OnDestroy {
  @Input() name = 'Guruprasad Bhosale';
  @Input() title = 'BUILDING THINGS THAT SHOULD PROBABLY EXIST.';
  @Input() handle = 'guruprasad-bhosale';
  @Input() avatarUrl = 'snf.jpg';
  @Input() githubUrl = 'https://github.com/Guruprasad-Bhosale';
  @Input() linkedinUrl = 'https://www.linkedin.com/in/guruprasad-bhosale';

  @ViewChild('cardWrapper') cardWrapper?: ElementRef<HTMLDivElement>;

  readonly isHovered = signal<boolean>(false);
  readonly imageError = signal<boolean>(false);
  readonly glowX = signal<number>(50);
  readonly glowY = signal<number>(50);
  readonly glowOpacity = signal<number>(0);
  readonly patternShiftX = signal<number>(0);
  readonly patternShiftY = signal<number>(0);

  private isReducedMotion = false;
  private rafId: number | null = null;
  private targetGlowX = 50;
  private targetGlowY = 50;
  private currentGlowX = 50;
  private currentGlowY = 50;

  ngOnInit(): void {
    if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
      this.isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
  }

  ngOnDestroy(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  onImageError(): void {
    this.imageError.set(true);
  }

  @HostListener('mousemove', ['$event'])
  onMouseMove(event: MouseEvent): void {
    if (this.isReducedMotion || !this.cardWrapper) return;

    const rect = this.cardWrapper.nativeElement.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Calculate percentage (0 - 100)
    this.targetGlowX = Math.max(0, Math.min(100, (x / rect.width) * 100));
    this.targetGlowY = Math.max(0, Math.min(100, (y / rect.height) * 100));

    // Subtle particle shift (-6px to +6px)
    const shiftX = ((this.targetGlowX - 50) / 50) * 6;
    const shiftY = ((this.targetGlowY - 50) / 50) * 6;
    this.patternShiftX.set(Number(shiftX.toFixed(2)));
    this.patternShiftY.set(Number(shiftY.toFixed(2)));

    this.glowOpacity.set(1);
    this.isHovered.set(true);

    this.startAnimationLoop();
  }

  @HostListener('mouseleave')
  onMouseLeave(): void {
    this.isHovered.set(false);
    this.glowOpacity.set(0);
    this.targetGlowX = 50;
    this.targetGlowY = 50;
    this.patternShiftX.set(0);
    this.patternShiftY.set(0);
    this.startAnimationLoop();
  }

  private startAnimationLoop(): void {
    if (this.rafId === null) {
      this.rafId = requestAnimationFrame(() => this.updateGlow());
    }
  }

  private updateGlow(): void {
    const ease = 0.12;
    this.currentGlowX += (this.targetGlowX - this.currentGlowX) * ease;
    this.currentGlowY += (this.targetGlowY - this.currentGlowY) * ease;

    this.glowX.set(Number(this.currentGlowX.toFixed(2)));
    this.glowY.set(Number(this.currentGlowY.toFixed(2)));

    const diff =
      Math.abs(this.targetGlowX - this.currentGlowX) +
      Math.abs(this.targetGlowY - this.currentGlowY);

    if (diff > 0.05) {
      this.rafId = requestAnimationFrame(() => this.updateGlow());
    } else {
      this.rafId = null;
    }
  }
}
