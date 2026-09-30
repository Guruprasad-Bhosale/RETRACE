import { ComponentFixture, TestBed } from '@angular/core/testing';
import { EvidenceChainViewComponent } from './evidence-chain-view.component';
import { EvidenceChain } from '../../../core/models/investigation.models';

describe('EvidenceChainViewComponent', () => {
  let component: EvidenceChainViewComponent;
  let fixture: ComponentFixture<EvidenceChainViewComponent>;

  const mockChain: EvidenceChain = {
    chain_id: 'chain_test_01',
    nodes: [
      {
        node_id: 'node_reg_01',
        node_type: 'REGRESSION_CLASSIFICATION',
        title: 'Functional Regression',
        phase_origin: 'PHASE_7_CLASSIFICATION',
        status: 'REGRESSION_CANDIDATE',
        evidence_ids: ['diff_01'],
        summary: 'Add to Cart button disabled',
        details: {},
      },
      {
        node_id: 'node_repro_01',
        node_type: 'REPRODUCTION',
        title: 'Autonomous Reproduction',
        phase_origin: 'PHASE_8_REPRODUCTION',
        status: 'REPRODUCED',
        evidence_ids: ['repro_01'],
        summary: 'Direct replay matched observed failure',
        details: {},
      },
      {
        node_id: 'node_src_01',
        node_type: 'SOURCE_LOCATION',
        title: 'Source Localization',
        phase_origin: 'PHASE_9_LOCALIZATION',
        status: 'LOCATED',
        evidence_ids: ['loc_01'],
        summary: 'cart.ts:42-50',
        details: {},
      },
    ],
    root_node_id: 'node_reg_01',
    leaf_node_id: 'node_src_01',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EvidenceChainViewComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(EvidenceChainViewComponent);
    component = fixture.componentInstance;
  });

  it('should render all nodes in the evidence chain', () => {
    fixture.componentRef.setInput('evidenceChain', mockChain);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Functional Regression');
    expect(el.textContent).toContain('Autonomous Reproduction');
    expect(el.textContent).toContain('Source Localization');
    expect(el.textContent).toContain('cart.ts:42-50');
  });

  it('should select node when clicked', () => {
    fixture.componentRef.setInput('evidenceChain', mockChain);
    fixture.detectChanges();

    component.selectNode(mockChain.nodes[1]);
    expect(component.selectedNode()).toEqual(mockChain.nodes[1]);
  });
});
