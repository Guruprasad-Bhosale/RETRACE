import { ComponentFixture, TestBed } from '@angular/core/testing';
import { StrokeTextComponent } from './stroke-text.component';

describe('StrokeTextComponent', () => {
  let component: StrokeTextComponent;
  let fixture: ComponentFixture<StrokeTextComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StrokeTextComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(StrokeTextComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the StrokeTextComponent', () => {
    expect(component).toBeTruthy();
  });

  it('should render SVG characters matching the input text', () => {
    fixture.componentRef.setInput('text', 'I like making difficult things exist.');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('I like making difficult things exist.');
    expect(component.characters().length).toBe('I like making difficult things exist.'.length);
  });

  it('should compute font style and viewBox properly', () => {
    fixture.componentRef.setInput('fontSize', 64);
    fixture.componentRef.setInput('fontWeight', 800);
    fixture.componentRef.setInput('letterSpacing', -2);
    fixture.detectChanges();

    const style = component.fontStyle();
    expect(style.fontSize).toBe('64px');
    expect(style.fontWeight).toBe(800);
    expect(style.letterSpacing).toBe('-2px');
    expect(component.viewBox()).toBeTruthy();
  });
});
