import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { App } from './app';
import { routes } from './app.routes';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideRouter(routes),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should render brand logo with RETRACE', async () => {
    const fixture = TestBed.createComponent(App);
    const router = TestBed.inject(Router);
    await router.navigate(['/dashboard']);
    fixture.detectChanges();
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('RETRACE');
  });

  it('should toggle mobile menu', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app.mobileMenuOpen()).toBe(false);
    app.toggleMobileMenu();
    expect(app.mobileMenuOpen()).toBe(true);
    app.closeMobileMenu();
    expect(app.mobileMenuOpen()).toBe(false);
  });

  it('should update active nav index', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    app.setActiveIndex(3);
    expect(app.activeNavIndex()).toBe(3);
  });

  it('should close mobile menu on Escape key', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    app.toggleMobileMenu();
    expect(app.mobileMenuOpen()).toBe(true);

    app.onKeyDown(new KeyboardEvent('keydown', { key: 'Escape' }));
    expect(app.mobileMenuOpen()).toBe(false);
  });

  it('should handle onMouseMove for ambient cursor glow safely', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(() => {
      app.onMouseMove(new MouseEvent('mousemove', { clientX: 150, clientY: 200 }));
    }).not.toThrow();
  });
});
