"""Reproduction Path Representation, Validation, and Deterministic Identity."""

import hashlib

from apps.worker.reproduction.errors import PathValidationError
from apps.worker.reproduction.models import ReproductionPath, ReproductionStep


def compute_reproduction_path_signature(seed_url: str, steps: list[ReproductionStep]) -> str:
    """Compute a deterministic hash representing the structural action path.

    Note: Volatile execution timestamps and non-deterministic UUIDs are excluded.
    """
    step_sigs = [s.compute_step_signature() for s in steps]
    raw = f"seed={seed_url}|steps={';'.join(step_sigs)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def validate_reproduction_path(path: ReproductionPath) -> None:
    """Perform structural and topological validation of a planned reproduction path.

    Raises:
        PathValidationError: If step sequence ordering, indices, or action structures are invalid.
    """
    if not path.seed_url:
        raise PathValidationError("Reproduction path must specify a non-empty seed_url.")

    for expected_idx, step in enumerate(path.steps):
        if step.step_index != expected_idx + 1:
            raise PathValidationError(
                f"Step ordering violation: expected step_index {expected_idx + 1}, got {step.step_index}"
            )
        if step.timeout_ms <= 0:
            raise PathValidationError(
                f"Step {step.step_index} has invalid non-positive timeout: {step.timeout_ms}"
            )
        if not step.action_type:
            raise PathValidationError(f"Step {step.step_index} is missing action_type.")
