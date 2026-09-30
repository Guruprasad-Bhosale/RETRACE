import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReportViewComponent } from './report-view.component';
import { EvidenceReport } from '../../../core/models/investigation.models';

describe('ReportViewComponent', () => {
  let component: ReportViewComponent;
  let fixture: ComponentFixture<ReportViewComponent>;

  const mockReport: EvidenceReport = {
    report_id: 'rep_cart_01',
    investigation_id: 'inv_cart_01',
    regression_id: 'clf_cart_01',
    title: 'Commerce Cart Add Disabled Regression',
    status: 'COMPLETE',
    summary: 'Executive summary of identified button disabled state.',
    markdown_content: '# Commerce Cart Report\n\nExecutive Summary\n\nIdentified button disabled state.',
    json_content: {
      investigation_id: 'inv_cart_01',
      title: 'Commerce Cart Add Disabled Regression',
      status: 'COMPLETE',
    },
    sections: [
      { section_id: 'sec_summary', section_number: 1, title: 'Executive Summary', content_markdown: 'Identified button disabled state.', evidence_ids: [] },
      { section_id: 'sec_regression', section_number: 2, title: 'Regression Classification', content_markdown: 'Functional regression candidate.', evidence_ids: ['clf_01'] },
    ],
    evidence_chain: {
      chain_id: 'chain_01',
      nodes: [],
    },
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReportViewComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ReportViewComponent);
    component = fixture.componentInstance;
  });

  it('should render report title and sections', () => {
    fixture.componentRef.setInput('report', mockReport);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Commerce Cart Add Disabled Regression');
    expect(el.textContent).toContain('Executive Summary');
    expect(el.textContent).toContain('Identified button disabled state.');
  });

  it('should toggle between Markdown and JSON view', () => {
    fixture.componentRef.setInput('report', mockReport);
    fixture.detectChanges();

    component.formatMode.set('json');
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('"investigation_id": "inv_cart_01"');
  });
});
