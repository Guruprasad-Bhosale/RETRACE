"""Deterministic Behavioral-to-Source Localization Engine.

Bridges empirical behavioral evidence (reproduction observations, classification details,
semantic differences) to concrete source code diff hunks and AST symbols without heuristics or guessing.
"""

from apps.worker.regression.models import RegressionCategory, RegressionClassification
from apps.worker.reproduction.models import ReproductionResult
from apps.worker.rootcause.ast.models import ASTFileIndex
from apps.worker.rootcause.config import LocalizationConfig
from apps.worker.rootcause.localization.regions import SourceRegionMatcher
from apps.worker.rootcause.models import (
    ASTSymbol,
    AttributionRelationshipType,
    DiffHunk,
    FileDiff,
    SourceLocation,
)


class LocalizedCandidate:
    """Internal candidate source match produced by behavioral localization."""

    def __init__(
        self,
        source_location: SourceLocation,
        symbol: ASTSymbol | None,
        diff_hunk: DiffHunk | None,
        relationship_type: AttributionRelationshipType,
        explanation: str,
        match_priority: int = 10,
    ):
        self.source_location = source_location
        self.symbol = symbol
        self.diff_hunk = diff_hunk
        self.relationship_type = relationship_type
        self.explanation = explanation
        self.match_priority = match_priority  # deterministic tie-breaker / specificity (higher = more specific)


class BehavioralLocalizer:
    """Deterministic behavioral-to-source localizer."""

    def __init__(self, config: LocalizationConfig | None = None):
        self.config = config or LocalizationConfig()

    def localize(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        diffs: list[FileDiff],
        ast_indices: dict[str, ASTFileIndex],
        repo_path: str = "",
    ) -> list[LocalizedCandidate]:
        """Map reproduced regression behavioral evidence to candidate source locations."""
        if classification.category == RegressionCategory.NON_REGRESSION:
            return []

        category = classification.category
        candidates: list[LocalizedCandidate] = []

        if category == RegressionCategory.NAVIGATION:
            candidates = self._localize_navigation(classification, reproduction, diffs, ast_indices, repo_path)
        elif category in (RegressionCategory.API_CONTRACT, RegressionCategory.FUNCTIONAL):
            candidates = self._localize_api_or_functional(classification, reproduction, diffs, ast_indices, repo_path)
        elif category == RegressionCategory.STATE:
            candidates = self._localize_state(classification, reproduction, diffs, ast_indices, repo_path)
        elif category == RegressionCategory.CALCULATION:
            candidates = self._localize_calculation(classification, reproduction, diffs, ast_indices, repo_path)
        elif category == RegressionCategory.ACCESSIBILITY:
            candidates = self._localize_accessibility(classification, reproduction, diffs, ast_indices, repo_path)
        elif category == RegressionCategory.PERFORMANCE:
            candidates = self._localize_performance(classification, reproduction, diffs, ast_indices, repo_path)
        elif category in (RegressionCategory.RUNTIME_ERROR, RegressionCategory.UI_BEHAVIOR):
            candidates = self._localize_runtime_or_ui(classification, reproduction, diffs, ast_indices, repo_path)
        else:
            candidates = self._localize_generic(classification, reproduction, diffs, ast_indices, repo_path)

        # Sort candidates deterministically: by priority desc, then file_path, start_line
        candidates.sort(
            key=lambda c: (
                -c.match_priority,
                c.source_location.file_path,
                c.source_location.start_line,
                c.relationship_type.value,
            )
        )
        return candidates[: self.config.max_candidate_locations]

    # --------------------------------------------------------------------------
    # Category Localizers
    # --------------------------------------------------------------------------

    def _localize_navigation(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        diffs: list[FileDiff],
        ast_indices: dict[str, ASTFileIndex],
        repo_path: str,
    ) -> list[LocalizedCandidate]:
        """Localize navigation failures (e.g. broken routes, 404 targets, modified links)."""
        candidates: list[LocalizedCandidate] = []
        evidence = classification.evidence
        canonical_subject = evidence.canonical_subject.lower()
        details = evidence.details or {}

        target_tokens = set()
        if canonical_subject:
            target_tokens.add(canonical_subject.strip("/"))
        for k in ("route", "url", "target_url", "href", "after_value", "before_value"):
            val = str(details.get(k) or "").strip("/").lower()
            if val and len(val) > 2:
                target_tokens.add(val)

        for fd in diffs:
            p = fd.primary_path()
            idx = ast_indices.get(p)
            for hunk in fd.hunks:
                hunk_text = "\n".join(dl.content for dl in hunk.lines).lower()
                matched_token = next((t for t in target_tokens if t in hunk_text or t in p.lower()), None)

                if matched_token:
                    # High confidence match
                    for loc, sym, h in SourceRegionMatcher.match_hunk_locations(fd, idx, repo_path):
                        if h == hunk:
                            rel = (
                                AttributionRelationshipType.AFFECTED_ROUTE
                                if (sym and sym.route_path) or "html" in p
                                else AttributionRelationshipType.DIRECTLY_CHANGED
                            )
                            candidates.append(
                                LocalizedCandidate(
                                    source_location=loc,
                                    symbol=sym,
                                    diff_hunk=h,
                                    relationship_type=rel,
                                    explanation=f"Route target or navigation path '{matched_token}' modified in diff hunk.",
                                    match_priority=30,
                                )
                            )

        if not candidates:
            candidates.extend(self._localize_generic(classification, reproduction, diffs, ast_indices, repo_path))
        return candidates

    def _localize_api_or_functional(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        diffs: list[FileDiff],
        ast_indices: dict[str, ASTFileIndex],
        repo_path: str,
    ) -> list[LocalizedCandidate]:
        """Localize API contract breaking changes and functional payload mismatches."""
        candidates: list[LocalizedCandidate] = []
        evidence = classification.evidence
        details = evidence.details or {}

        subject = evidence.canonical_subject.lower()
        endpoint = str(details.get("endpoint") or details.get("url") or "").lower()

        tokens = set()
        if subject:
            tokens.add(subject)
        if endpoint:
            tokens.add(endpoint.strip("/"))
            for seg in endpoint.split("/"):
                if len(seg) > 2:
                    tokens.add(seg)

        # Check for schema/payload keys
        for k in ("key", "field", "body", "payload"):
            if k in details and isinstance(details[k], str):
                tokens.add(details[k].lower())

        for fd in diffs:
            p = fd.primary_path()
            idx = ast_indices.get(p)
            for loc, sym, hunk in SourceRegionMatcher.match_hunk_locations(fd, idx, repo_path):
                hunk_text = (loc.snippet or "").lower()

                # Check if symbol is route handler matching endpoint
                if sym and sym.route_path:
                    norm_sym_route = sym.route_path.strip("/").lower()
                    if any(t in norm_sym_route or norm_sym_route in t for t in tokens if len(t) > 2):
                        candidates.append(
                            LocalizedCandidate(
                                source_location=loc,
                                symbol=sym,
                                diff_hunk=hunk,
                                relationship_type=AttributionRelationshipType.AFFECTED_ROUTE,
                                explanation=f"API endpoint handler '{sym.name}' modified in diff.",
                                match_priority=28,
                            )
                        )
                        continue

                # Check if hunk contains matching payload keys or endpoint strings
                matched_token = next((t for t in tokens if len(t) > 2 and t in hunk_text), None)
                if matched_token:
                    candidates.append(
                        LocalizedCandidate(
                            source_location=loc,
                            symbol=sym,
                            diff_hunk=hunk,
                            relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
                            explanation=f"API contract token/key '{matched_token}' modified in source diff.",
                            match_priority=25,
                        )
                    )

        if not candidates:
            candidates.extend(self._localize_generic(classification, reproduction, diffs, ast_indices, repo_path))
        return candidates

    def _localize_state(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        diffs: list[FileDiff],
        ast_indices: dict[str, ASTFileIndex],
        repo_path: str,
    ) -> list[LocalizedCandidate]:
        """Localize state persistence and storage loss regressions."""
        candidates: list[LocalizedCandidate] = []
        subject = classification.evidence.canonical_subject.lower()

        keywords = {"cart", "state", "storage", "localstorage", "sessionstorage", "persist", "hydrate", "quantity", "session"}
        if subject:
            keywords.add(subject)

        for fd in diffs:
            p = fd.primary_path()
            idx = ast_indices.get(p)
            for loc, sym, hunk in SourceRegionMatcher.match_hunk_locations(fd, idx, repo_path):
                hunk_text = (loc.snippet or "").lower()

                # Match state key or localStorage operations
                if any(kw in hunk_text for kw in keywords):
                    rel = (
                        AttributionRelationshipType.AFFECTED_SYMBOL
                        if sym
                        else AttributionRelationshipType.DIRECTLY_CHANGED
                    )
                    candidates.append(
                        LocalizedCandidate(
                            source_location=loc,
                            symbol=sym,
                            diff_hunk=hunk,
                            relationship_type=rel,
                            explanation="State persistence or hydration logic modified in source diff.",
                            match_priority=24,
                        )
                    )

        if not candidates:
            candidates.extend(self._localize_generic(classification, reproduction, diffs, ast_indices, repo_path))
        return candidates

    def _localize_calculation(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        diffs: list[FileDiff],
        ast_indices: dict[str, ASTFileIndex],
        repo_path: str,
    ) -> list[LocalizedCandidate]:
        """Localize calculation discrepancies (tax, total, discount, math formulas)."""
        candidates: list[LocalizedCandidate] = []
        subject = classification.evidence.canonical_subject.lower()
        keywords = {"tax", "total", "subtotal", "calc", "discount", "sum", "price", "rate", "formula", "amount"}
        if subject:
            keywords.add(subject)

        for fd in diffs:
            p = fd.primary_path()
            idx = ast_indices.get(p)
            for loc, sym, hunk in SourceRegionMatcher.match_hunk_locations(fd, idx, repo_path):
                hunk_text = (loc.snippet or "").lower()
                if any(kw in hunk_text or (sym and kw in sym.name.lower()) for kw in keywords):
                    rel = (
                        AttributionRelationshipType.AFFECTED_SYMBOL
                        if sym
                        else AttributionRelationshipType.DIRECTLY_CHANGED
                    )
                    candidates.append(
                        LocalizedCandidate(
                            source_location=loc,
                            symbol=sym,
                            diff_hunk=hunk,
                            relationship_type=rel,
                            explanation="Calculation logic or financial computation formula modified in source diff.",
                            match_priority=26,
                        )
                    )

        if not candidates:
            candidates.extend(self._localize_generic(classification, reproduction, diffs, ast_indices, repo_path))
        return candidates

    def _localize_accessibility(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        diffs: list[FileDiff],
        ast_indices: dict[str, ASTFileIndex],
        repo_path: str,
    ) -> list[LocalizedCandidate]:
        """Localize accessibility regressions (missing labels, stripped aria attributes)."""
        candidates: list[LocalizedCandidate] = []
        subject = classification.evidence.canonical_subject.lower()
        keywords = {"aria", "label", "required", "role", "alt", "for=", "input", "form"}

        for fd in diffs:
            p = fd.primary_path()
            idx = ast_indices.get(p)
            for loc, sym, hunk in SourceRegionMatcher.match_hunk_locations(fd, idx, repo_path):
                hunk_text = (loc.snippet or "").lower()
                if any(kw in hunk_text for kw in keywords) or (subject and subject in hunk_text):
                    candidates.append(
                        LocalizedCandidate(
                            source_location=loc,
                            symbol=sym,
                            diff_hunk=hunk,
                            relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
                            explanation="Accessibility attribute or form element definition modified in source template.",
                            match_priority=25,
                        )
                    )

        if not candidates:
            candidates.extend(self._localize_generic(classification, reproduction, diffs, ast_indices, repo_path))
        return candidates

    def _localize_performance(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        diffs: list[FileDiff],
        ast_indices: dict[str, ASTFileIndex],
        repo_path: str,
    ) -> list[LocalizedCandidate]:
        """Localize performance regressions (latency spikes, blocking sync loops)."""
        candidates: list[LocalizedCandidate] = []
        keywords = {"sleep", "delay", "query", "sync", "search", "time", "timeout", "wait", "blocking"}

        for fd in diffs:
            p = fd.primary_path()
            idx = ast_indices.get(p)
            for loc, sym, hunk in SourceRegionMatcher.match_hunk_locations(fd, idx, repo_path):
                hunk_text = (loc.snippet or "").lower()
                if any(kw in hunk_text for kw in keywords):
                    candidates.append(
                        LocalizedCandidate(
                            source_location=loc,
                            symbol=sym,
                            diff_hunk=hunk,
                            relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
                            explanation="Potential blocking computation or latency-inducing logic modified in source diff.",
                            match_priority=20,
                        )
                    )

        if not candidates:
            candidates.extend(self._localize_generic(classification, reproduction, diffs, ast_indices, repo_path))
        return candidates

    def _localize_runtime_or_ui(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        diffs: list[FileDiff],
        ast_indices: dict[str, ASTFileIndex],
        repo_path: str,
    ) -> list[LocalizedCandidate]:
        """Localize runtime console errors or UI behavior differences."""
        candidates: list[LocalizedCandidate] = []
        details = classification.evidence.details or {}
        err_msg = str(details.get("message") or "").lower()

        for fd in diffs:
            p = fd.primary_path()
            idx = ast_indices.get(p)
            for loc, sym, hunk in SourceRegionMatcher.match_hunk_locations(fd, idx, repo_path):
                hunk_text = (loc.snippet or "").lower()
                if err_msg and any(w in hunk_text for w in err_msg.split() if len(w) > 4):
                    candidates.append(
                        LocalizedCandidate(
                            source_location=loc,
                            symbol=sym,
                            diff_hunk=hunk,
                            relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
                            explanation="Source change matches error token in runtime console diff.",
                            match_priority=22,
                        )
                    )

        if not candidates:
            candidates.extend(self._localize_generic(classification, reproduction, diffs, ast_indices, repo_path))
        return candidates

    def _localize_generic(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        diffs: list[FileDiff],
        ast_indices: dict[str, ASTFileIndex],
        repo_path: str,
    ) -> list[LocalizedCandidate]:
        """Fallback candidate extraction across all diff hunks."""
        candidates: list[LocalizedCandidate] = []
        for fd in diffs:
            p = fd.primary_path()
            idx = ast_indices.get(p)
            for loc, sym, hunk in SourceRegionMatcher.match_hunk_locations(fd, idx, repo_path):
                candidates.append(
                    LocalizedCandidate(
                        source_location=loc,
                        symbol=sym,
                        diff_hunk=hunk,
                        relationship_type=AttributionRelationshipType.RELATED_CHANGE,
                        explanation=f"Co-changed source region in modified file '{p}'.",
                        match_priority=5,
                    )
                )
        return candidates
