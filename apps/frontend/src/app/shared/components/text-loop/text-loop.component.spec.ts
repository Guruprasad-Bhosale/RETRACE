import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TextLoopComponent } from './text-loop.component';

describe('TextLoopComponent', () => {
  let component: TextLoopComponent;
  let fixture: ComponentFixture<TextLoopComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TextLoopComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(TextLoopComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the TextLoopComponent', () => {
    expect(component).toBeTruthy();
  });

  it('should generate a valid SVG path data string for shape=wave', () => {
    expect(component.pathData()).toContain('M -320');
    expect(component.pathData()).toContain('Q');
  });

  it('should compute unit text with default separator', () => {
    expect(component.unitText()).toContain('TRACE');
    expect(component.unitText()).toContain('✦');
  });

  it('should support pointer pause and resume on hover', () => {
    expect(() => {
      component.onPointerEnter();
      component.onPointerLeave();
    }).not.toThrow();
  });
});
