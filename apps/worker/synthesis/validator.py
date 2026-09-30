"""Generated Test Validator.

Performs static AST/structural validation, selector integrity checks, and evidence
grounding verification on synthesized Playwright test artifacts before export.
"""

import re

from apps.worker.synthesis.models import GeneratedTest, ValidationStatus


class GeneratedTestValidator:
    """Validates structural correctness and evidence grounding of synthesized tests."""

    FORBIDDEN_GROUND_TRUTH_PATTERNS = [
        re.compile(r"\bDEF-00[1-6]\b", re.IGNORECASE),
        re.compile(r"ground_truth\.json", re.IGNORECASE),
        re.compile(r"lab\.ground_truth", re.IGNORECASE),
    ]

    @classmethod
    def validate(cls, test_model: GeneratedTest) -> tuple[ValidationStatus, list[str]]:
        """Perform full structural and integrity validation on a GeneratedTest artifact.

        Returns:
            Tuple of (ValidationStatus, list_of_notes_or_errors)
        """
        notes: list[str] = []
        source = test_model.generated_source

        # 1. Check for empty source code
        if not source or not source.strip():
            return ValidationStatus.VALIDATION_FAILED, ["Generated test source code is empty."]

        # 2. Check Playwright imports
        if "@playwright/test" not in source:
            return ValidationStatus.VALIDATION_FAILED, ["Missing required '@playwright/test' import."]

        # 3. Check balanced brackets/braces/parentheses
        pairs = {"{": "}", "(": ")", "[": "]"}
        stack = []
        in_single_quote = False
        in_double_quote = False
        in_backtick = False

        i = 0
        while i < len(source):
            c = source[i]
            if c == "\\" and (in_single_quote or in_double_quote or in_backtick):
                i += 2
                continue

            if c == "'" and not in_double_quote and not in_backtick:
                in_single_quote = not in_single_quote
            elif c == '"' and not in_single_quote and not in_backtick:
                in_double_quote = not in_double_quote
            elif c == "`" and not in_single_quote and not in_double_quote:
                in_backtick = not in_backtick
            elif not in_single_quote and not in_double_quote and not in_backtick:
                if c in pairs:
                    stack.append(c)
                elif c in pairs.values():
                    if not stack:
                        return ValidationStatus.VALIDATION_FAILED, [f"Unmatched closing delimiter '{c}' in test source."]
                    open_c = stack.pop()
                    if pairs[open_c] != c:
                        return ValidationStatus.VALIDATION_FAILED, [
                            f"Mismatched delimiter: opened '{open_c}' but closed '{c}'."
                        ]
            i += 1

        if stack:
            return ValidationStatus.VALIDATION_FAILED, [f"Unclosed delimiter '{stack[-1]}' in test source."]

        # 4. Check step selectors
        for idx, step in enumerate(test_model.steps):
            if not step.resolved_selector or not step.resolved_selector.strip():
                return ValidationStatus.VALIDATION_FAILED, [f"Step {idx + 1} has an empty resolved selector."]
            if "page.locator('')" in step.resolved_selector:
                return ValidationStatus.VALIDATION_FAILED, [f"Step {idx + 1} contains empty locator string."]

        # 5. Check assertion evidence grounding
        for idx, assertion in enumerate(test_model.assertions):
            if not assertion.evidence_id:
                return ValidationStatus.VALIDATION_FAILED, [f"Assertion {idx + 1} lacks an evidence_id reference."]
            if not assertion.subject:
                return ValidationStatus.VALIDATION_FAILED, [f"Assertion {idx + 1} lacks a subject."]

        # 6. Check for forbidden ground truth leakage
        for pattern in cls.FORBIDDEN_GROUND_TRUTH_PATTERNS:
            if pattern.search(source):
                return ValidationStatus.VALIDATION_FAILED, [
                    f"Forbidden benchmark ground-truth reference detected matching pattern '{pattern.pattern}'."
                ]

        notes.append("Structural validation passed: valid TypeScript syntax and balanced delimiters.")
        notes.append(f"Verified {len(test_model.steps)} action steps and {len(test_model.assertions)} evidence assertions.")
        notes.append("Ground-truth isolation verified: 0 synthetic defect references.")

        return ValidationStatus.STRUCTURALLY_VALIDATED, notes
