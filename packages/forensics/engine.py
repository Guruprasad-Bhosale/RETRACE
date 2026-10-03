"""Forensic Intelligence & Evidence Graph 2.0 Engine.

Master coordinator unifying multi-phase evidence, prompt-injection sanitization,
explicit hypothesis evaluation, falsification conditions, transparent confidence scoring, and DAG graph generation.
"""


from apps.worker.investigation.models import InvestigationResult
from packages.forensics.confidence import ConfidenceCalculator
from packages.forensics.falsification import FalsificationEngine
from packages.forensics.graph_builder import EvidenceGraphBuilder
from packages.forensics.hypothesis_engine import HypothesisEngine
from packages.forensics.models import (
    ForensicEvidenceItem,
    ForensicEvidenceType,
    ForensicInvestigationExplanation,
    compute_deterministic_evidence_id,
)
from packages.forensics.sanitizer import ForensicSanitizer


class ForensicIntelligenceEngine:
    """Orchestrates forensic evidence analysis, hypothesis elimination, and DAG graph synthesis."""

    @classmethod
    def explain_investigation(cls, investigation: InvestigationResult) -> ForensicInvestigationExplanation:
        """Derive complete forensic explanation package from an authoritative InvestigationResult."""
        inv_id = investigation.investigation_id
        classification = investigation.classification
        root_cause = investigation.root_cause
        reproduction = investigation.reproduction
        test = investigation.generated_test

        raw_title = getattr(classification, "title", None) or classification.reason or f"{classification.category.value} regression"
        raw_desc = getattr(classification, "description", None) or classification.reason

        title = ForensicSanitizer.sanitize_string(raw_title)
        description = ForensicSanitizer.sanitize_string(raw_desc)


        # 1. Collect and sanitize forensic evidence items
        raw_items: list[ForensicEvidenceItem] = []

        # Observation & Diff Evidence
        diff_id = compute_deterministic_evidence_id(inv_id, ForensicEvidenceType.DOM_OBSERVATION, "diff")
        raw_items.append(
            ForensicEvidenceItem(
                id=diff_id,
                investigation_id=inv_id,
                evidence_type=ForensicEvidenceType.DOM_OBSERVATION,
                source="Browser Observation Engine",
                observation=f"Observed behavioral divergence: {title}",
                payload={"category": classification.category.value, "reason": classification.reason},
                confidence_weight=0.90,
            )
        )

        # Source Attribution Evidence (if present)
        source_file: str | None = None
        source_line: int | None = None
        commit_hash: str | None = None
        source_func: str | None = None

        if root_cause and root_cause.primary_attribution:
            attr = root_cause.primary_attribution
            loc = attr.source_location
            source_file = loc.file_path
            source_line = loc.start_line
            source_func = getattr(loc, "symbol_name", getattr(loc, "function_name", None))
            commit_hash = attr.commit.commit_hash if attr.commit else None

            weight = getattr(attr, "confidence_score", 0.95 if attr.relationship_type.value == "DIRECTLY_CHANGED" else 0.80)
            src_id = compute_deterministic_evidence_id(inv_id, ForensicEvidenceType.AST_DIFF, f"{source_file}:{source_line}")
            raw_items.append(
                ForensicEvidenceItem(
                    id=src_id,
                    investigation_id=inv_id,
                    evidence_type=ForensicEvidenceType.AST_DIFF,
                    source="AST Provenance & Git Engine",
                    observation=f"Attributed to {source_file}:{source_line} ({source_func or 'top-level'})",
                    payload={"file": source_file, "line": source_line, "commit": commit_hash},
                    confidence_weight=weight,
                )
            )

        # Reproduction Evidence (if present)
        has_repro = bool(reproduction and getattr(reproduction.status, "value", reproduction.status) == "REPRODUCED")
        repro_failed = bool(reproduction and getattr(reproduction.status, "value", reproduction.status) == "FAILED")
        if reproduction:
            rep_id = compute_deterministic_evidence_id(inv_id, ForensicEvidenceType.REPRODUCTION, "playwright_replay")
            raw_items.append(
                ForensicEvidenceItem(
                    id=rep_id,
                    investigation_id=inv_id,
                    evidence_type=ForensicEvidenceType.REPRODUCTION,
                    source="Playwright Execution Harness",
                    observation=f"Reproduction status: {getattr(reproduction.status, 'value', reproduction.status)}",
                    payload={"status": getattr(reproduction.status, "value", reproduction.status)},
                    confidence_weight=1.0 if has_repro else 0.5,
                )
            )

        # Sanitize all evidence items against adversarial prompt injection
        evidence_items = [ForensicSanitizer.sanitize_evidence_item(item) for item in raw_items]
        evidence_catalog = {e.id: e for e in evidence_items}

        # 2. Formulate and eliminate hypotheses
        primary_hypothesis, eliminated_alternatives = HypothesisEngine.evaluate_hypotheses(
            investigation_id=inv_id,
            category=classification.category.value,
            title=title,
            description=description,
            evidence_items=evidence_items,
            has_reproduction=has_repro,
            reproduction_failed=repro_failed,
            source_file=source_file,
            source_function=source_func,
        )


        # 3. Generate testable falsification condition
        falsification = FalsificationEngine.generate_falsification_condition(
            hypothesis=primary_hypothesis,
            source_file=source_file,
            line_number=source_line,
            commit_hash=commit_hash,
        )

        # 4. Calculate transparent confidence
        confidence = ConfidenceCalculator.evaluate(
            primary_hypothesis=primary_hypothesis,
            evidence_catalog=evidence_catalog,
            has_reproduction=has_repro,
            has_source_match=bool(source_file),
        )

        # 5. Build deterministic Evidence DAG Graph
        reproduction_code = getattr(test, "generated_source", getattr(test, "code", None)) if test else None
        evidence_graph = EvidenceGraphBuilder.build_graph(
            investigation_id=inv_id,
            category=classification.category.value,
            title=title,
            hypothesis=primary_hypothesis,
            evidence_items=evidence_items,
            source_file=source_file,
            source_line=source_line,
            commit_hash=commit_hash,
            reproduction_code=reproduction_code,
        )

        # 6. Validate all evidence references (Fail-Closed)
        all_referenced_ids = list(primary_hypothesis.supporting_evidence_ids) + list(
            primary_hypothesis.contradicting_evidence_ids
        )
        for alt in eliminated_alternatives:
            all_referenced_ids.extend(alt.evidence_references)
        for node in evidence_graph.nodes:
            all_referenced_ids.extend(node.evidence_item_ids)

        ForensicSanitizer.validate_evidence_references(
            referenced_ids=all_referenced_ids,
            valid_evidence_catalog=evidence_catalog,
        )

        # 7. Assemble final explanation
        provenance_chain = [
            f"Observation: {title}",
            f"Classification: {classification.category.value} (id: {classification.classification_id})",
            f"Attribution: {source_file}:{source_line}" if source_file else "Attribution: Inferred from state diff",
            f"Reproduction: {'Confirmed' if has_repro else 'Pending'}",
            f"Root Cause: {primary_hypothesis.title}",
        ]

        return ForensicInvestigationExplanation(
            investigation_id=inv_id,
            root_cause_summary=primary_hypothesis.description,
            root_cause_status=primary_hypothesis.status.value,
            primary_hypothesis=primary_hypothesis,
            eliminated_alternatives=eliminated_alternatives,
            evidence_graph=evidence_graph,
            confidence=confidence,
            falsification=falsification,
            provenance_chain=provenance_chain,
            evidence_graph_available=True,
        )
