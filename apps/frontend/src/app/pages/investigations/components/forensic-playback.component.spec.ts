import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach } from 'vitest';
import { ForensicPlaybackComponent } from './forensic-playback.component';

describe('ForensicPlaybackComponent', () => {
  let component: ForensicPlaybackComponent;
  let fixture: ComponentFixture<ForensicPlaybackComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ForensicPlaybackComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ForensicPlaybackComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should initialize at step 0 and step through on nextStep()', () => {
    expect(component).toBeTruthy();
    expect(component.currentStep()).toBe(0);

    component.nextStep();
    expect(component.currentStep()).toBe(1);

    component.previousStep();
    expect(component.currentStep()).toBe(0);
  });

  it('should set specific step when setStep is invoked', () => {
    component.setStep(3);
    expect(component.currentStep()).toBe(3);
    expect(component.steps[3].label).toBe('HYPOTHESIZE');
  });
});
