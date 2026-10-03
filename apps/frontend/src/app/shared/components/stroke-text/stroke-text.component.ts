import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
  computed,
  effect,
  inject,
  input,
  signal,
  NgZone,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
  gsap.registerPlugin(ScrollTrigger);
}

export interface StrokeTextBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

@Component({
  selector: 'app-stroke-text',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './stroke-text.component.html',
  styleUrl: './stroke-text.component.css',
})
export class StrokeTextComponent implements AfterViewInit, OnDestroy {
  private readonly ngZone = inject(NgZone);

  readonly text = input<string>('Draw Attention');
  readonly strokeColor = input<string>('#A78BFA');
  readonly fillColor = input<string>('#F8FAFC');
  readonly strokeWidth = input<number | string>(1.4);
  readonly drawDuration = input<number>(1.12);
  readonly fillDelay = input<number>(0.14);
  readonly delay = input<number>(0);
  readonly stagger = input<number>(0.028);
  readonly ease = input<string>('power2.out');
  readonly trigger = input<'mount' | 'hover' | 'scroll' | 'loop'>('mount');
  readonly fillMode = input<'fade' | 'wipe' | 'none'>('wipe');
  readonly fontSize = input<number | string>(128);
  readonly fontWeight = input<number | string>(800);
  readonly letterSpacing = input<number | string>(-4);
  readonly wordSpacing = input<number | string>(0);
  readonly lineHeight = input<number | string>(1.15);
  readonly reverse = input<boolean>(false);
  readonly align = input<'left' | 'center' | 'right'>('left');
  readonly className = input<string>('');
  readonly style = input<Record<string, any>>({});

  @ViewChild('rootRef') rootRef?: ElementRef<HTMLElement>;
  @ViewChild('strokeTextRef') strokeTextRef?: ElementRef<SVGTextElement>;
  @ViewChild('wipeRectRef') wipeRectRef?: ElementRef<SVGRectElement>;

  private readonly rawId = Math.random().toString(36).substring(2, 9);
  readonly wipeId = `stroke-text-wipe-${this.rawId}`;

  readonly box = signal<StrokeTextBox | null>(null);

  readonly lines = computed(() => {
    const raw = String(this.text() ?? '');
    return raw.split('\n');
  });

  readonly characters = computed(() => Array.from(String(this.text() ?? '').replace(/\n/g, '')));

  readonly numFontSize = computed(() => {
    const fs = this.fontSize();
    return typeof fs === 'string' ? parseFloat(fs) || 128 : fs;
  });

  readonly numStrokeWidth = computed(() => {
    const sw = this.strokeWidth();
    return typeof sw === 'string' ? parseFloat(sw) || 1.4 : sw;
  });

  readonly numLineHeight = computed(() => {
    const lh = this.lineHeight();
    if (typeof lh === 'string') {
      const parsed = parseFloat(lh);
      return isNaN(parsed) ? 1.15 : parsed;
    }
    return lh ?? 1.15;
  });

  readonly preserveAspectRatio = computed(() => {
    const a = this.align();
    if (a === 'center') return 'xMidYMid meet';
    if (a === 'right') return 'xMaxYMid meet';
    return 'xMinYMid meet';
  });

  readonly fontStyle = computed(() => {
    const fs = typeof this.fontSize() === 'number' ? `${this.fontSize()}px` : this.fontSize();
    const ls =
      typeof this.letterSpacing() === 'number'
        ? `${this.letterSpacing()}px`
        : this.letterSpacing();
    const ws =
      typeof this.wordSpacing() === 'number' ? `${this.wordSpacing()}px` : this.wordSpacing();
    return {
      fontSize: fs,
      fontWeight: this.fontWeight(),
      letterSpacing: ls,
      wordSpacing: ws,
      fontFamily: 'inherit',
    };
  });

  readonly hostStyle = computed(() => {
    const fs = this.numFontSize();
    const lineCount = this.lines().length;
    const totalHeight = Math.round(fs * (1 + (lineCount - 1) * this.numLineHeight()) * 1.35);
    return {
      ...this.style(),
      '--stroke-text-height': `${totalHeight}px`,
    };
  });

  readonly viewBox = computed(() => {
    const b = this.box();
    const fs = this.numFontSize();
    if (b) {
      return `${b.x} ${b.y} ${b.width} ${b.height}`;
    }
    const maxLineLength = Math.max(...this.lines().map((l) => l.length), 10);
    const approxWidth = Math.max(600, maxLineLength * fs * 0.6);
    const lineCount = this.lines().length;
    const approxHeight = fs * (1 + (lineCount - 1) * this.numLineHeight()) * 1.35;
    return `0 ${-fs} ${approxWidth} ${approxHeight}`;
  });

  private timeline: gsap.core.Timeline | null = null;
  private scrollTriggerInstance: ScrollTrigger | null = null;
  private removeHoverListener: (() => void) | null = null;
  private isDestroyed = false;

  constructor() {
    effect(() => {
      // Track input changes to remeasure & setup animations
      this.text();
      this.fontSize();
      this.fontWeight();
      this.letterSpacing();
      this.wordSpacing();
      this.lineHeight();
      this.strokeWidth();

      if (typeof window !== 'undefined') {
        setTimeout(() => this.measure(), 0);
      }
    });

    effect(() => {
      // Track styling & animation timing changes
      this.strokeColor();
      this.fillColor();
      this.drawDuration();
      this.fillDelay();
      this.delay();
      this.stagger();
      this.ease();
      this.trigger();
      this.fillMode();
      this.reverse();

      if (this.box()) {
        this.setupAnimation();
      }
    });
  }

  lineChars(line: string): string[] {
    return Array.from(line);
  }

  ngAfterViewInit(): void {
    if (typeof window === 'undefined') return;

    this.measure();

    if (typeof document !== 'undefined' && (document as any).fonts?.ready) {
      (document as any).fonts.ready
        .then(() => {
          if (!this.isDestroyed) {
            this.measure();
          }
        })
        .catch(() => {});
    }
  }

  ngOnDestroy(): void {
    this.isDestroyed = true;
    this.cleanupAnimation();
  }

  private measure(): void {
    if (this.isDestroyed || !this.strokeTextRef?.nativeElement) return;

    let bbox: DOMRect | SVGRect | null = null;
    try {
      bbox = this.strokeTextRef.nativeElement.getBBox();
    } catch {
      // In non-browser environments or jsdom, safely fallback
      return;
    }

    if (!bbox || !bbox.width) return;

    const strokeW = Number(this.numStrokeWidth()) || 1.4;
    const pad = Math.max(strokeW, 2);
    const next: StrokeTextBox = {
      x: bbox.x - pad,
      y: bbox.y - pad,
      width: bbox.width + pad * 2,
      height: bbox.height + pad * 2,
    };

    const prev = this.box();
    if (
      !prev ||
      Math.abs(prev.x - next.x) >= 0.5 ||
      Math.abs(prev.width - next.width) >= 0.5 ||
      Math.abs(prev.y - next.y) >= 0.5
    ) {
      this.box.set(next);
      setTimeout(() => {
        if (!this.isDestroyed) {
          this.setupAnimation();
        }
      }, 0);
    }
  }

  private cleanupAnimation(): void {
    if (this.removeHoverListener) {
      this.removeHoverListener();
      this.removeHoverListener = null;
    }
    if (this.scrollTriggerInstance) {
      this.scrollTriggerInstance.kill();
      this.scrollTriggerInstance = null;
    }
    if (this.timeline) {
      this.timeline.kill();
      this.timeline = null;
    }
    const root = this.rootRef?.nativeElement;
    if (root) {
      const strokes = root.querySelectorAll('[data-stroke-char]');
      const fills = root.querySelectorAll('[data-fill-char]');
      const wipe = this.wipeRectRef?.nativeElement;
      const targets = [...Array.from(strokes), ...Array.from(fills), wipe].filter(Boolean);
      gsap.killTweensOf(targets);
    }
  }

  private setupAnimation(): void {
    this.cleanupAnimation();

    const root = this.rootRef?.nativeElement;
    const currentBox = this.box();
    if (typeof window === 'undefined' || !root || !currentBox) return;

    const strokes = root.querySelectorAll('[data-stroke-char]');
    const fills = root.querySelectorAll('[data-fill-char]');
    const wipe = this.wipeRectRef?.nativeElement;
    if (!strokes.length) return;

    const dash = Math.max(this.numFontSize() * 7, 200);
    const fillEnabled = this.fillMode() !== 'none';
    const useWipe = fillEnabled && this.fillMode() === 'wipe';
    const fillDuration = Math.max(0.35, this.drawDuration() * 0.45);
    const staggerConfig = this.reverse()
      ? { each: this.stagger(), from: 'end' }
      : this.stagger();
    const targets = [...Array.from(strokes), ...Array.from(fills), wipe].filter(Boolean);

    const setStart = () => {
      gsap.killTweensOf(targets);
      gsap.set(strokes, { strokeDasharray: dash, strokeDashoffset: dash });
      gsap.set(fills, { opacity: useWipe ? 1 : 0 });
      if (wipe) gsap.set(wipe, { attr: { width: 0 } });
    };

    const setEnd = () => {
      gsap.killTweensOf(targets);
      gsap.set(strokes, { strokeDasharray: dash, strokeDashoffset: 0 });
      gsap.set(fills, { opacity: fillEnabled ? 1 : 0 });
      if (wipe) gsap.set(wipe, { attr: { width: fillEnabled ? currentBox.width : 0 } });
    };

    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
      setEnd();
      return;
    }

    const build = () => {
      setStart();
      const tl = gsap.timeline({
        paused: true,
        repeat: this.trigger() === 'loop' ? -1 : 0,
        repeatDelay: this.trigger() === 'loop' ? 0.9 : 0,
        defaults: { overwrite: 'auto' },
      });

      const startOffset = Math.max(0, this.delay());
      tl.to(
        strokes,
        {
          strokeDashoffset: 0,
          duration: this.drawDuration(),
          ease: this.ease(),
          stagger: staggerConfig as any,
        },
        startOffset
      );

      if (useWipe && wipe) {
        tl.to(
          wipe,
          {
            attr: { width: currentBox.width },
            duration: fillDuration,
            ease: 'power2.inOut',
          },
          startOffset + this.drawDuration() + this.fillDelay()
        );
      } else if (fillEnabled) {
        tl.to(
          fills,
          {
            opacity: 1,
            duration: fillDuration,
            ease: 'power2.out',
            stagger: staggerConfig as any,
          },
          startOffset + this.drawDuration() + this.fillDelay()
        );
      }

      return tl;
    };

    if (this.trigger() === 'hover') {
      setEnd();
      const play = () => {
        this.timeline?.kill();
        this.timeline = build();
        this.timeline.play(0);
      };
      root.addEventListener('pointerenter', play);
      this.removeHoverListener = () => root.removeEventListener('pointerenter', play);
    } else {
      this.timeline = build();
      if (this.trigger() === 'scroll') {
        if (typeof ScrollTrigger !== 'undefined' && typeof ScrollTrigger.create === 'function') {
          this.scrollTriggerInstance = ScrollTrigger.create({
            trigger: root,
            start: 'top 82%',
            once: true,
            onEnter: () => this.timeline?.play(0),
          });
        } else {
          this.timeline.play(0);
        }
      } else {
        this.timeline.play(0);
      }
    }
  }
}
