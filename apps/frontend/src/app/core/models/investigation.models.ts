/**
 * RETRACE Investigation Domain Models for Frontend Command Center.
 *
 * Strongly typed TypeScript interfaces mirroring backend Phase 7-10 contracts.
 */

export type InvestigationStatus = 'COMPLETED' | 'PARTIAL' | 'INCONCLUSIVE' | 'FAILED';

export type RegressionCategory =
  | 'FUNCTIONAL'
  | 'NAVIGATION'
  | 'API_CONTRACT'
  | 'STATE'
  | 'CALCULATION'
  | 'ACCESSIBILITY'
  | 'PERFORMANCE'
  | 'UI_BEHAVIOR'
  | 'RUNTIME_ERROR'
  | 'UNKNOWN'
  | 'NON_REGRESSION';

export type RootCauseStatus =
  | 'LOCATED'
  | 'PARTIALLY_LOCATED'
  | 'CANDIDATE_ONLY'
  | 'INCONCLUSIVE'
  | 'UNSUPPORTED';

export type CommitAttributionType =
  | 'CAUSAL_COMMIT'
  | 'INTRODUCING_COMMIT'
  | 'MODIFYING_COMMIT'
  | 'RELATED_COMMIT'
  | 'NO_ATTRIBUTABLE_COMMIT';

export type AttributionRelationshipType =
  | 'DIRECTLY_CHANGED'
  | 'AFFECTED_SYMBOL'
  | 'AFFECTED_CALL_SITE'
  | 'AFFECTED_ROUTE'
  | 'AFFECTED_CONFIGURATION'
  | 'ANCESTOR_CHANGE'
  | 'RELATED_CHANGE'
  | 'INSUFFICIENT_EVIDENCE';

export type ValidationStatus =
  | 'VALIDATED'
  | 'STRUCTURALLY_VALIDATED'
  | 'VALIDATION_FAILED'
  | 'NOT_VALIDATED';

export type SynthesisStatus =
  | 'SYNTHESIZED'
  | 'PARTIALLY_SYNTHESIZED'
  | 'INCOMPLETE'
  | 'UNSUPPORTED';

export type ReproductionStatus =
  | 'PLANNED'
  | 'RUNNING'
  | 'REPRODUCED'
  | 'NOT_REPRODUCED'
  | 'BLOCKED'
  | 'FAILED'
  | 'INCONCLUSIVE';

export interface InvestigationSummaryItem {
  investigation_id: string;
  analysis_id: string;
  regression_id: string;
  category: string;
  status: InvestigationStatus;
  title: string;
  has_generated_test: boolean;
  source_location?: string | null;
  commit_hash?: string | null;
}

export interface ArtifactReference {
  id: string;
  kind: string;
  storage_uri: string;
  mime_type: string;
  size_bytes: number;
  sha256_hash?: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface ClassificationEvidence {
  difference_id: string;
  canonical_subject: string;
  observation_a_id?: string | null;
  observation_b_id?: string | null;
  artifact_references: ArtifactReference[];
  details: Record<string, unknown>;
}

export interface RegressionClassification {
  classification_id: string;
  difference_id: string;
  status: string;
  category: RegressionCategory;
  rule_id: string;
  reason: string;
  evidence: ClassificationEvidence;
  created_at: string;
}

export interface ReproductionStep {
  step_index: number;
  action_type: string;
  raw_target?: string | null;
  stable_target_identity?: string | null;
  target_role?: string | null;
  accessible_name?: string | null;
  target_strategy: string;
  value?: string | null;
  timeout_ms: number;
  metadata?: Record<string, unknown>;
}

export interface ReproductionPath {
  path_id: string;
  trajectory_id: string;
  classification_id: string;
  difference_id: string;
  seed_url: string;
  steps: ReproductionStep[];
  path_signature: string;
  observation_ids: string[];
}

export interface ReproductionVerification {
  expected_difference_id: string;
  expected_classification_id: string;
  expected_rule_id: string;
  expected_category: string;
  match_status: string;
  observed_match: boolean;
  matched_evidence: string[];
  mismatched_evidence: string[];
  notes: string;
}

export interface ReproductionObservation {
  reproduction_observation_id: string;
  version_id: string;
  step_index: number;
  url: string;
  http_status?: number | null;
  page_title?: string | null;
  console_errors_count: number;
  duration_ms: number;
  action_success: boolean;
  error_message?: string | null;
}

export interface ReproductionEvidence {
  attempt_id: string;
  observations_a: ReproductionObservation[];
  observations_b: ReproductionObservation[];
  sample_measurements_ms_a: number[];
  sample_measurements_ms_b: number[];
  artifact_references: ArtifactReference[];
}

export interface ReproductionAttemptResult {
  attempt_id: string;
  attempt_number: number;
  strategy: string;
  status: ReproductionStatus;
  verification?: ReproductionVerification | null;
  evidence: ReproductionEvidence;
  duration_ms: number;
}

export interface ReproductionResult {
  reproduction_id: string;
  classification_id: string;
  difference_id: string;
  rule_id: string;
  category: string;
  status: ReproductionStatus;
  strategy: string;
  path: ReproductionPath;
  attempts: ReproductionAttemptResult[];
  final_verification?: ReproductionVerification | null;
  total_duration_ms: number;
}

export interface SourceLocation {
  repository_path: string;
  commit_hash?: string | null;
  file_path: string;
  symbol_name?: string | null;
  symbol_kind?: string | null;
  start_line: number;
  start_column: number;
  end_line: number;
  end_column: number;
  snippet?: string | null;
}

export interface DiffLine {
  change_type: string;
  content: string;
  old_line_number?: number | null;
  new_line_number?: number | null;
}

export interface DiffHunk {
  old_start: number;
  old_lines: number;
  new_start: number;
  new_lines: number;
  header: string;
  lines: DiffLine[];
  added_lines: number[];
  deleted_lines: number[];
}

export interface CommitMetadata {
  commit_hash: string;
  author_name: string;
  author_email: string;
  timestamp: string;
  message: string;
  parent_hashes: string[];
  is_merge: boolean;
}

export interface RootCauseAttribution {
  attribution_id: string;
  source_location: SourceLocation;
  relationship_type: AttributionRelationshipType;
  commit?: CommitMetadata | null;
  commit_attribution_type: CommitAttributionType;
  diff_hunk?: DiffHunk | null;
  explanation: string;
}

export interface RootCauseResult {
  root_cause_id: string;
  classification_id: string;
  difference_id: string;
  reproduction_id?: string | null;
  category: string;
  status: RootCauseStatus;
  primary_attribution?: RootCauseAttribution | null;
  attributions: RootCauseAttribution[];
  candidate_locations: SourceLocation[];
  diagnostics?: Record<string, unknown>;
}

export interface TestStep {
  step_index: number;
  action_type: string;
  raw_target?: string | null;
  resolved_selector: string;
  selector_strategy: string;
  value?: string | null;
  timeout_ms: number;
  description: string;
}

export interface TestAssertion {
  assertion_id: string;
  category: string;
  assertion_type: string;
  subject: string;
  expected_value: unknown;
  actual_value_observed?: unknown;
  operator: string;
  tolerance?: number | null;
  manual_review_required: boolean;
  evidence_id: string;
  reasoning: string;
}

export interface TestProvenance {
  classification_id: string;
  difference_id: string;
  reproduction_id?: string | null;
  root_cause_id?: string | null;
  source_locations: string[];
  commit_hashes: string[];
}

export interface GeneratedTest {
  test_id: string;
  regression_id: string;
  reproduction_id?: string | null;
  root_cause_id?: string | null;
  framework: string;
  language: string;
  target_version: string;
  title: string;
  description: string;
  steps: TestStep[];
  assertions: TestAssertion[];
  provenance: TestProvenance;
  status: SynthesisStatus;
  validation_status: ValidationStatus;
  generated_source: string;
  validation_notes: string[];
}

export interface EvidenceChainNode {
  node_id: string;
  node_type: string;
  title: string;
  phase_origin: string;
  status: string;
  evidence_ids: string[];
  summary: string;
  details: Record<string, unknown>;
}

export interface EvidenceChain {
  chain_id: string;
  nodes: EvidenceChainNode[];
  root_node_id?: string | null;
  leaf_node_id?: string | null;
}

export interface ReportSection {
  section_id: string;
  section_number: number;
  title: string;
  content_markdown: string;
  evidence_ids: string[];
}

export interface EvidenceReport {
  report_id: string;
  investigation_id?: string | null;
  regression_id: string;
  title: string;
  status: string;
  summary: string;
  sections: ReportSection[];
  evidence_chain: EvidenceChain;
  markdown_content: string;
  json_content: Record<string, unknown>;
}

export interface InvestigationProvenance {
  analysis_id: string;
  classification_id: string;
  difference_id: string;
  reproduction_id?: string | null;
  root_cause_id?: string | null;
  test_id?: string | null;
  report_id?: string | null;
  artifact_references: ArtifactReference[];
}

export interface InvestigationResult {
  investigation_id: string;
  analysis_id: string;
  regression_id: string;
  classification: RegressionClassification;
  reproduction?: ReproductionResult | null;
  root_cause?: RootCauseResult | null;
  generated_test?: GeneratedTest | null;
  report: EvidenceReport;
  artifacts: ArtifactReference[];
  provenance: InvestigationProvenance;
  status: InvestigationStatus;
  created_at: string;
}

// -----------------------------------------------------------------------------
// Phase 18: Forensic Intelligence & Evidence Graph 2.0 Models
// -----------------------------------------------------------------------------

export type ForensicEvidenceType =
  | 'dom_observation'
  | 'network_observation'
  | 'console_observation'
  | 'visual_diff'
  | 'accessibility_diff'
  | 'performance_diff'
  | 'state_diff'
  | 'reproduction'
  | 'git_diff'
  | 'ast_diff'
  | 'source_reference'
  | 'test_result';

export type EdgeType =
  | 'SUPPORTS'
  | 'CONTRADICTS'
  | 'CAUSED_BY'
  | 'CORRELATES_WITH'
  | 'REPRODUCES'
  | 'DERIVED_FROM'
  | 'LOCATED_AT'
  | 'INVALIDATES';

export type HypothesisStatus =
  | 'PROPOSED'
  | 'SUPPORTED'
  | 'WEAKENED'
  | 'ELIMINATED'
  | 'CONFIRMED'
  | 'UNRESOLVED';

export type HypothesisCategory =
  | 'CALCULATION_LOGIC'
  | 'DOM_RENDER_LOGIC'
  | 'API_CONTRACT'
  | 'TIMING_RACE_CONDITION'
  | 'STYLING_FORMATTING'
  | 'STATE_PERSISTENCE'
  | 'NAVIGATION_ROUTING'
  | 'UNKNOWN';

export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT';

export interface ForensicEvidenceItem {
  id: string;
  investigation_id: string;
  evidence_type: ForensicEvidenceType;
  source: string;
  observation: string;
  payload?: Record<string, unknown>;
  artifact_reference?: ArtifactReference | null;
  confidence_weight: number;
  supports: string[];
  contradicts: string[];
  is_untrusted_input: boolean;
  timestamp: string;
}

export interface EvidenceGraphNode {
  node_id: string;
  node_type: string;
  title: string;
  status: string;
  evidence_item_ids: string[];
  confidence_score: number;
  metadata?: Record<string, unknown>;
}

export interface EvidenceGraphEdge {
  edge_id: string;
  source_node_id: string;
  target_node_id: string;
  relationship: EdgeType;
  weight: number;
  explanation: string;
}

export interface EvidenceGraph {
  graph_id: string;
  investigation_id: string;
  nodes: EvidenceGraphNode[];
  edges: EvidenceGraphEdge[];
  deterministic_hash: string;
  created_at: string;
}

export interface ForensicHypothesis {
  hypothesis_id: string;
  title: string;
  description: string;
  category: HypothesisCategory;
  status: HypothesisStatus;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  elimination_reason?: string | null;
  score: number;
}

export interface ConfidenceAssessment {
  level: ConfidenceLevel;
  score: number;
  supporting_count: number;
  contradicting_count: number;
  unresolved_count: number;
  rationale: string;
}

export interface FalsificationCondition {
  condition_id: string;
  statement: string;
  testable_verification: string;
  potential_confounders: string[];
}

export interface AlternativeExplanation {
  alternative_id: string;
  title: string;
  category: HypothesisCategory;
  status: HypothesisStatus;
  elimination_reason: string;
  evidence_references: string[];
}

export interface ForensicInvestigationExplanation {
  investigation_id: string;
  root_cause_summary: string;
  root_cause_status: string;
  primary_hypothesis: ForensicHypothesis;
  eliminated_alternatives: AlternativeExplanation[];
  evidence_graph: EvidenceGraph;
  confidence: ConfidenceAssessment;
  falsification: FalsificationCondition;
  provenance_chain: string[];
  evidence_graph_available: boolean;
  created_at: string;
}

export interface InvestigationReplaySnapshot {
  investigation_id: string;
  schema_version: string;
  analysis_version: string;
  snapshot_hash: string;
  evidence_items: ForensicEvidenceItem[];
  observations: Record<string, unknown>[];
  diffs: Record<string, unknown>[];
  hypotheses: ForensicHypothesis[];
  source_references: Record<string, unknown>[];
  reproduction_results: Record<string, unknown>[];
  deterministic_config: Record<string, unknown>;
  created_at: string;
}

export interface ReplayResult {
  replay_id: string;
  investigation_id: string;
  snapshot_hash: string;
  analysis_version: string;
  graph_hash: string;
  hypothesis_hash: string;
  explanation_hash: string;
  status: string;
  is_reproducible: boolean;
  divergence_details: string[];
  replayed_explanation?: ForensicInvestigationExplanation | null;
  created_at: string;
}

export interface GraphDiffItem {
  diff_type: string;
  node_or_edge_id: string;
  details: string;
  severity: string;
}

export interface InvestigationComparisonResult {
  investigation_a_id: string;
  investigation_b_id: string;
  shared_evidence_count: number;
  unique_evidence_a_count: number;
  unique_evidence_b_count: number;
  root_cause_matches: boolean;
  hypothesis_matches: boolean;
  graph_diff: GraphDiffItem[];
  explanation_diff: string[];
  created_at: string;
}


