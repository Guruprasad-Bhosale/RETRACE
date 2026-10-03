import { Component, Input, signal, Output, EventEmitter, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface PlaybackStep {
  index: number;
  label: string;
  phase: string;
  description: string;
}

@Component({
  selector: 'app-forensic-playback',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="card p-4 border-2 border-theme-primary bg-theme-surface">
      <!-- Playback Controls Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 mb-3 border-b border-theme-primary/30">
        <div class="flex items-center space-x-2">
          <span class="w-2.5 h-2.5 rounded-full bg-accent-orange"></span>
          <h4 class="text-xs font-mono uppercase font-bold text-theme-primary">
            Forensic Investigation Playback
          </h4>
        </div>

        <!-- Buttons -->
        <div class="flex items-center space-x-2">
          <button
            (click)="previousStep()"
            [disabled]="currentStep() === 0"
            class="px-2.5 py-1 rounded border border-theme-primary bg-theme-base text-xs font-mono disabled:opacity-30 hover:border-accent-orange transition-colors"
            aria-label="Previous step"
          >
            &larr; PREV
          </button>
          <button
            (click)="togglePlay()"
            class="px-3 py-1 rounded bg-accent-orange text-white text-xs font-mono font-bold hover:bg-accent-orange/90 transition-colors"
            [attr.aria-label]="isPlaying() ? 'Pause playback' : 'Start playback'"
          >
            {{ isPlaying() ? 'PAUSE' : 'PLAY' }}
          </button>
          <button
            (click)="nextStep()"
            [disabled]="currentStep() >= steps.length - 1"
            class="px-2.5 py-1 rounded border border-theme-primary bg-theme-base text-xs font-mono disabled:opacity-30 hover:border-accent-orange transition-colors"
            aria-label="Next step"
          >
            NEXT &rarr;
          </button>
        </div>
      </div>

      <!-- Scrubber Stepper -->
      <div class="grid grid-cols-2 sm:grid-cols-6 gap-2 mb-3">
        <button
          *ngFor="let step of steps; let i = index"
          (click)="setStep(i)"
          [class.border-accent-orange]="currentStep() === i"
          [class.bg-accent-orange/10]="currentStep() === i"
          [class.text-accent-orange]="currentStep() === i"
          class="p-2 rounded border border-theme-primary/40 bg-theme-base text-left text-xs font-mono transition-all hover:border-accent-orange"
        >
          <span class="text-[9px] block text-theme-muted uppercase font-bold">STEP 0{{ i + 1 }}</span>
          <span class="font-bold truncate block">{{ step.label }}</span>
        </button>
      </div>

      <!-- Current Step Description -->
      <div class="p-3 rounded bg-theme-base border border-theme-primary/20 text-xs font-mono">
        <div class="flex items-center justify-between text-theme-muted mb-1">
          <span class="text-[10px] uppercase font-bold text-accent-orange">
            PHASE: {{ steps[currentStep()].phase }}
          </span>
          <span class="text-[10px]">
            STEP {{ currentStep() + 1 }} OF {{ steps.length }}
          </span>
        </div>
        <p class="text-theme-primary">
          {{ steps[currentStep()].description }}
        </p>
      </div>
    </div>
  `,
})
export class ForensicPlaybackComponent implements OnDestroy {
  readonly currentStep = signal<number>(0);
  readonly isPlaying = signal<boolean>(false);
  private timer: any = null;

  @Output() stepChange = new EventEmitter<number>();

  readonly steps: PlaybackStep[] = [
    {
      index: 0,
      label: 'OBSERVE',
      phase: 'Phase 4: Browser Exploration',
      description: 'Captured baseline vs. candidate state snapshots and interactive element observations.',
    },
    {
      index: 1,
      label: 'DIFF',
      phase: 'Phase 6: Difference Engine',
      description: 'Extracted semantic DOM, accessibility, network, and visual state divergence.',
    },
    {
      index: 2,
      label: 'CLASSIFY',
      phase: 'Phase 7: Regression Classifier',
      description: 'Applied deterministic classification rules to verify true regression candidate.',
    },
    {
      index: 3,
      label: 'HYPOTHESIZE',
      phase: 'Phase 18: Hypothesis Engine',
      description: 'Formulated primary diagnostic hypothesis and eliminated disproven alternatives.',
    },
    {
      index: 4,
      label: 'LOCALIZE',
      phase: 'Phase 9: AST Root Cause',
      description: 'Traced behavioral regression to exact AST modified symbols and Git commit diffs.',
    },
    {
      index: 5,
      label: 'REPRODUCE',
      phase: 'Phase 8/10: Synthesis Replay',
      description: 'Synthesized executable Playwright reproduction test verifying regression output.',
    },
  ];

  setStep(index: number): void {
    if (index >= 0 && index < this.steps.length) {
      this.currentStep.set(index);
      this.stepChange.emit(index);
    }
  }

  nextStep(): void {
    if (this.currentStep() < this.steps.length - 1) {
      this.setStep(this.currentStep() + 1);
    } else {
      this.pause();
    }
  }

  previousStep(): void {
    if (this.currentStep() > 0) {
      this.setStep(this.currentStep() - 1);
    }
  }

  togglePlay(): void {
    if (this.isPlaying()) {
      this.pause();
    } else {
      this.play();
    }
  }

  play(): void {
    this.isPlaying.set(true);
    this.timer = setInterval(() => {
      if (this.currentStep() < this.steps.length - 1) {
        this.nextStep();
      } else {
        this.setStep(0);
      }
    }, 2500);
  }

  pause(): void {
    this.isPlaying.set(false);
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  ngOnDestroy(): void {
    this.pause();
  }
}
