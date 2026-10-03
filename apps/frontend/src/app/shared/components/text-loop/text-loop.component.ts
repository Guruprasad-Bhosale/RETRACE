import {
  AfterViewInit,
  Component,
  ElementRef,
  HostListener,
  Input,
  OnChanges,
  OnDestroy,
  OnInit,
  SimpleChanges,
  ViewChild,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { gsap } from 'gsap';

const VIEW_W = 1200;
const VIEW_H = 320;
const CX = VIEW_W / 2;
const CY = VIEW_H / 2;
const EDGE_PAD = 6;

@Component({
  selector: 'app-text-loop',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './text-loop.component.html',
  styleUrl: './text-loop.component.css',
})
export class TextLoopComponent implements OnInit, AfterViewInit, OnChanges, OnDestroy {
  @Input() text = 'TRACE ✦ OBSERVE ✦ COMPARE ✦ EVIDENCE ✦ ROOT CAUSE ✦ REPRODUCE';
  @Input() shape: 'wave' | 'circle' | 'infinity' | 'arch' | 'line' = 'wave';
  @Input() path?: string;
  @Input() speed = 65;
  @Input() direction: 'forward' | 'reverse' = 'forward';
  @Input() separator = '✦';
  @Input() curviness = 55;
  @Input() fontSize = 38;
  @Input() fontWeight = 800;
  @Input() letterSpacing = 3;
  @Input() uppercase = true;
  @Input() color = '#e7e5e4';
  @Input() separatorColor = '#FF5A1F';
  @Input() ribbon = true;
  @Input() ribbonColor = 'rgba(255, 90, 31, 0.05)';
  @Input() ribbonWidth = 64;
  @Input() pauseOnHover = true;

  @ViewChild('rootRef') rootRef?: ElementRef<HTMLDivElement>;
  @ViewChild('pathRef') pathRef?: ElementRef<SVGPathElement>;
  @ViewChild('measureRef') measureRef?: ElementRef<SVGTextElement>;
  @ViewChild('headRef') headRef?: ElementRef<SVGTextPathElement>;
  @ViewChild('tailRef') tailRef?: ElementRef<SVGTextPathElement>;

  readonly pathId = `text-loop-${Math.random().toString(36).substring(2, 9)}`;
  readonly pathData = signal<string>('');
  readonly unitText = signal<string>('');
  readonly loopText = signal<string>('');
  readonly fitLength = signal<number | undefined>(undefined);

  private tween: gsap.core.Tween | null = null;
  private pathLength = 0;
  private isReducedMotion = false;
  private isDestroyed = false;

  ngOnInit(): void {
    if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
      this.isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    this.computeUnitAndPath();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (
      changes['text'] ||
      changes['shape'] ||
      changes['path'] ||
      changes['curviness'] ||
      changes['ribbonWidth'] ||
      changes['separator'] ||
      changes['uppercase']
    ) {
      this.computeUnitAndPath();
      if (typeof window !== 'undefined') {
        setTimeout(() => this.measureAndAnimate(), 20);
      }
    }
  }

  ngAfterViewInit(): void {
    if (typeof window !== 'undefined') {
      this.measureAndAnimate();
      if (typeof document !== 'undefined' && (document as any).fonts?.ready) {
        (document as any).fonts.ready
          .then(() => {
            if (!this.isDestroyed) {
              this.measureAndAnimate();
            }
          })
          .catch(() => {});
      }
    }
  }

  ngOnDestroy(): void {
    this.isDestroyed = true;
    this.killAnimation();
  }

  @HostListener('pointerenter')
  onPointerEnter(): void {
    if (this.pauseOnHover && this.tween) {
      this.tween.pause();
    }
  }

  @HostListener('pointerleave')
  onPointerLeave(): void {
    if (this.pauseOnHover && this.tween) {
      this.tween.resume();
    }
  }

  private computeUnitAndPath(): void {
    const base = this.uppercase ? String(this.text).toUpperCase() : String(this.text);
    const gap = this.separator ? `\u00A0\u00A0${this.separator}\u00A0\u00A0` : '\u00A0\u00A0\u00A0';
    this.unitText.set(`${base}${gap}`);
    this.pathData.set(this.path || this.buildPath(this.shape, this.curviness, this.ribbonWidth));
  }

  private buildPath(shape: string, curviness: number, ribbonWidth: number): string {
    const c = Math.max(0, curviness);
    const room = Math.max(20, CY - Math.max(0, ribbonWidth) / 2 - EDGE_PAD);

    switch (shape) {
      case 'circle': {
        const r = Math.min(90 + c * 0.95, room);
        return `M ${CX - r} ${CY} A ${r} ${r} 0 1 1 ${CX + r} ${CY} A ${r} ${r} 0 1 1 ${CX - r} ${CY} Z`;
      }
      case 'infinity': {
        const r = 150 + c * 1.4;
        const h = Math.min(60 + c * 0.95, room);
        return [
          `M ${CX} ${CY}`,
          `C ${CX + r * 0.55} ${CY - h} ${CX + r} ${CY - h} ${CX + r} ${CY}`,
          `C ${CX + r} ${CY + h} ${CX + r * 0.55} ${CY + h} ${CX} ${CY}`,
          `C ${CX - r * 0.55} ${CY - h} ${CX - r} ${CY - h} ${CX - r} ${CY}`,
          `C ${CX - r} ${CY + h} ${CX - r * 0.55} ${CY + h} ${CX} ${CY}`,
          'Z',
        ].join(' ');
      }
      case 'arch': {
        const rise = Math.min(120 + c * 1.1, room * 2);
        return `M 120 ${CY + rise / 2} Q ${CX} ${CY - rise * 1.5} ${VIEW_W - 120} ${CY + rise / 2}`;
      }
      case 'line':
        return `M -320 ${CY} L ${VIEW_W + 320} ${CY}`;
      case 'wave':
      default: {
        const a = Math.min(c * 1.8, room * 1.6);
        return `M -320 ${CY} Q -160 ${CY - a} 0 ${CY} T 320 ${CY} T 640 ${CY} T 960 ${CY} T 1280 ${CY} T ${VIEW_W + 320} ${CY}`;
      }
    }
  }

  private measureAndAnimate(): void {
    if (!this.pathRef || !this.measureRef) return;
    const pathEl = this.pathRef.nativeElement;
    const measureEl = this.measureRef.nativeElement;

    let length = 0;
    let unitWidth = 0;
    try {
      length = pathEl.getTotalLength();
      unitWidth = measureEl.getComputedTextLength();
    } catch {
      return;
    }
    if (!length) return;

    this.pathLength = length;
    const reps = unitWidth > 0 ? Math.max(1, Math.round(length / unitWidth)) : 1;
    this.loopText.set(this.unitText().repeat(reps));
    this.fitLength.set(length || undefined);

    this.startGSAPAnimation();
  }

  private startGSAPAnimation(): void {
    this.killAnimation();

    const head = this.headRef?.nativeElement;
    const tail = this.tailRef?.nativeElement;
    if (!head || !tail || !this.pathLength) return;

    const apply = (offset: number) => {
      const partner = offset >= 0 ? offset - this.pathLength : offset + this.pathLength;
      head.setAttribute('startOffset', String(offset));
      tail.setAttribute('startOffset', String(partner));
    };

    apply(0);

    if (this.isReducedMotion || this.speed <= 0) {
      return;
    }

    const state = { offset: 0 };
    this.tween = gsap.to(state, {
      offset: this.direction === 'reverse' ? -this.pathLength : this.pathLength,
      duration: this.pathLength / this.speed,
      ease: 'none',
      repeat: -1,
      onUpdate: () => apply(state.offset),
    });
  }

  private killAnimation(): void {
    if (this.tween) {
      this.tween.kill();
      this.tween = null;
    }
  }
}
