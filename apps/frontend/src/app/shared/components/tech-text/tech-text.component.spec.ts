import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TechTextComponent } from './tech-text.component';

describe('TechTextComponent', () => {
  let component: TechTextComponent;
  let fixture: ComponentFixture<TechTextComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TechTextComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(TechTextComponent);
    component = fixture.componentInstance;
    component.text = 'RETRACE.';
    fixture.detectChanges();
  });

  it('should create the TechText component', () => {
    expect(component).toBeTruthy();
  });

  it('should render canvas element with tech-text-canvas class', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const canvas = compiled.querySelector('canvas.tech-text-canvas');
    expect(canvas).toBeTruthy();
  });

  it('should have correct default inputs and update on text change', () => {
    expect(component.text).toBe('RETRACE.');
    component.text = 'AUTONOMOUS';
    component.ngOnChanges({});
    expect(component.text).toBe('AUTONOMOUS');
  });
});
