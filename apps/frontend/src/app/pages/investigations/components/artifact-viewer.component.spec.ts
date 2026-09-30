import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ArtifactViewerComponent } from './artifact-viewer.component';
import { ArtifactReference } from '../../../core/models/investigation.models';

describe('ArtifactViewerComponent', () => {
  let component: ArtifactViewerComponent;
  let fixture: ComponentFixture<ArtifactViewerComponent>;

  const mockArtifacts: ArtifactReference[] = [
    {
      id: 'art-01',
      kind: 'SCREENSHOT_DOM',
      storage_uri: 'file:///storage/screenshot.png',
      mime_type: 'image/png',
      size_bytes: 204800,
      sha256_hash: 'a1b2c3d4e5f6',
      created_at: '2026-09-30T10:00:00Z',
    },
    {
      id: 'art-02',
      kind: 'GENERATED_TEST',
      storage_uri: 'file:///storage/test.spec.ts',
      mime_type: 'text/typescript',
      size_bytes: 1200,
      sha256_hash: 'f6e5d4c3b2a1',
      created_at: '2026-09-30T10:00:00Z',
    },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ArtifactViewerComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ArtifactViewerComponent);
    component = fixture.componentInstance;
  });

  it('should render artifact gallery cards', () => {
    fixture.componentRef.setInput('artifacts', mockArtifacts);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('SCREENSHOT_DOM');
    expect(el.textContent).toContain('GENERATED_TEST');
    expect(el.textContent).toContain('MIME: image/png');
    expect(el.textContent).toContain('MIME: text/typescript');
  });

  it('should format file sizes correctly', () => {
    expect(component.formatBytes(0)).toBe('0 B');
    expect(component.formatBytes(1024)).toBe('1 KB');
    expect(component.formatBytes(1048576)).toBe('1 MB');
  });

  it('should identify screenshot artifact types correctly', () => {
    expect(component.isScreenshot(mockArtifacts[0])).toBe(true);
    expect(component.isScreenshot(mockArtifacts[1])).toBe(false);
  });
});
