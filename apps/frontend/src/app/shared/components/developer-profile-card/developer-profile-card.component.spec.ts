import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DeveloperProfileCardComponent } from './developer-profile-card.component';

describe('DeveloperProfileCardComponent', () => {
  let component: DeveloperProfileCardComponent;
  let fixture: ComponentFixture<DeveloperProfileCardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DeveloperProfileCardComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(DeveloperProfileCardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the DeveloperProfileCardComponent', () => {
    expect(component).toBeTruthy();
  });

  it('should render the developer name, title and handle', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Guruprasad Bhosale');
    expect(compiled.textContent).toContain('BUILDING THINGS THAT SHOULD PROBABLY EXIST.');
    expect(compiled.textContent).toContain('@guruprasad-bhosale');
  });

  it('should contain verified GitHub and LinkedIn links', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const github = compiled.querySelector('a[href="https://github.com/Guruprasad-Bhosale"]');
    const linkedin = compiled.querySelector('a[href="https://www.linkedin.com/in/guruprasad-bhosale"]');

    expect(github).toBeTruthy();
    expect(github?.getAttribute('target')).toBe('_blank');
    expect(linkedin).toBeTruthy();
    expect(linkedin?.getAttribute('target')).toBe('_blank');
  });

  it('should activate behind glow and particle shift on mouse move', () => {
    const mouseEvent = new MouseEvent('mousemove', {
      clientX: 50,
      clientY: 50,
    });

    component.onMouseMove(mouseEvent);
    expect(component.isHovered()).toBe(true);
    expect(component.glowOpacity()).toBe(1);
  });

  it('should reset behind glow on mouse leave', () => {
    component.onMouseLeave();
    expect(component.isHovered()).toBe(false);
    expect(component.glowOpacity()).toBe(0);
    expect(component.patternShiftX()).toBe(0);
    expect(component.patternShiftY()).toBe(0);
  });

  it('should handle image error gracefully', () => {
    component.onImageError();
    expect(component.imageError()).toBe(true);
  });
});
