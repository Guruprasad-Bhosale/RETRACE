import { ComponentFixture, TestBed } from '@angular/core/testing';
import { LandingPageComponent } from './landing.component';
import { provideRouter } from '@angular/router';
import { Router } from '@angular/router';

describe('LandingPageComponent', () => {
  let component: LandingPageComponent;
  let fixture: ComponentFixture<LandingPageComponent>;
  let router: Router;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LandingPageComponent],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(LandingPageComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
  });

  it('should create the LandingPageComponent', () => {
    expect(component).toBeTruthy();
  });

  it('should render all primary editorial sections with unified grid including developer and cta', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('#hero')).toBeTruthy();
    expect(compiled.querySelector('#mission')).toBeTruthy();
    expect(compiled.querySelector('#how-it-works')).toBeTruthy();
    expect(compiled.querySelector('#investigation')).toBeTruthy();
    expect(compiled.querySelector('#developer')).toBeTruthy();
    expect(compiled.querySelector('#cta')).toBeTruthy();
  });

  it('should render the TextLoopComponent', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const textLoop = compiled.querySelector('app-text-loop');
    expect(textLoop).toBeTruthy();
  });

  it('should display THE MIND BEHIND IT and authentic Gen-Z engineering narrative', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const text = compiled.textContent || '';
    expect(text).toContain('THE MIND BEHIND IT');
    expect(text).not.toContain('THE BUILDER');
    expect(text).not.toContain('HUMAN OPERATOR');
    expect(text).toContain('I like making difficult things exist.');
    expect(text).toContain('Curious by default.');
    expect(text).toContain('RETRACE happens to be one of those projects.');
    expect(text).not.toContain('passionate');
    expect(text).not.toContain('visionary');
    expect(text).not.toContain('results-driven');
  });

  it('should render the personal philosophy quote integrated inside developer section with strict attribution', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const developerSection = compiled.querySelector('#developer');
    expect(developerSection).toBeTruthy();
    expect(developerSection?.textContent).toContain('An idiot in motion is better than a genius at rest.');
    expect(developerSection?.textContent).toContain('me.');
  });

  it('should trigger laser scan transition and navigate to dashboard on enterRetrace()', () => {
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);
    component.enterRetrace();
    expect(component.isTransitioning()).toBe(true);
  });

  it('should support switching investigation milestones', () => {
    component.selectInvestigationStep(3);
    expect(component.activeInvestigationIndex()).toBe(3);
    expect(component.investigationSteps[3].title).toBe('ROOT CAUSE');
  });

  it('should render the DeveloperProfileCardComponent in developer section', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const profileCard = compiled.querySelector('app-developer-profile-card');
    expect(profileCard).toBeTruthy();
  });

  it('should contain verified developer profile links with secure target attributes', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const githubLinks = compiled.querySelectorAll('a[href="https://github.com/Guruprasad-Bhosale"]');
    const linkedinLinks = compiled.querySelectorAll('a[href="https://www.linkedin.com/in/guruprasad-bhosale"]');
    
    expect(githubLinks.length).toBeGreaterThan(0);
    expect(githubLinks[0].getAttribute('target')).toBe('_blank');
    expect(githubLinks[0].getAttribute('rel')).toContain('noopener');

    expect(linkedinLinks.length).toBeGreaterThan(0);
    expect(linkedinLinks[0].getAttribute('target')).toBe('_blank');
    expect(linkedinLinks[0].getAttribute('rel')).toContain('noopener');
  });

  it('should render the developer title directly inside h2 with StrokeTextComponent animation', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const developerSection = compiled.querySelector('#developer');
    expect(developerSection?.textContent).not.toContain('[ HUMAN OPERATOR // 01 ]');
    expect(developerSection?.textContent).not.toContain('THE BUILDER');
    
    const h2 = developerSection?.querySelector('h2');
    expect(h2).toBeTruthy();
    expect(h2?.textContent).toContain('I like making difficult things exist.');
    expect(developerSection?.querySelector('app-stroke-text')).toBeTruthy();
  });

  it('should not contain any development placeholder artifacts', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const pageText = compiled.textContent || '';
    expect(pageText).not.toContain('[SLOT:');
    expect(pageText).not.toContain('PLACEHOLDER');
    expect(pageText).not.toContain('MISSION_DESCRIPTION');
    expect(pageText).not.toContain('HERO_OVERSIZED_HEADLINE');
    expect(pageText).not.toContain('undefined');
  });
});
