"""Unit Tests for Reproduction Path Validation and Signatures."""

from uuid import uuid4

import pytest

from apps.worker.reproduction.errors import PathValidationError
from apps.worker.reproduction.models import ReproductionPath, ReproductionStep
from apps.worker.reproduction.path import (
    validate_reproduction_path,
)
from packages.domain.models import ActionType


def test_validate_reproduction_path_success():
    """Verify valid reproduction path passes validation."""
    steps = [
        ReproductionStep(
            step_index=1,
            action_type=ActionType.CLICK,
            stable_target_identity="#btn1",
        ),
        ReproductionStep(
            step_index=2,
            action_type=ActionType.TYPE,
            stable_target_identity="#inp1",
            value="hello",
        ),
    ]
    path = ReproductionPath(
        path_id="path-valid",
        trajectory_id=uuid4(),
        classification_id="class-1",
        difference_id="diff-1",
        seed_url="http://localhost:3000/",
        steps=steps,
        path_signature="sig-1",
    )
    validate_reproduction_path(path)


def test_validate_reproduction_path_step_order_violation():
    """Verify step ordering violation raises PathValidationError."""
    steps = [
        ReproductionStep(
            step_index=2,  # Should start at 1
            action_type=ActionType.CLICK,
            stable_target_identity="#btn1",
        ),
    ]
    path = ReproductionPath(
        path_id="path-invalid",
        trajectory_id=uuid4(),
        classification_id="class-1",
        difference_id="diff-1",
        seed_url="http://localhost:3000/",
        steps=steps,
        path_signature="sig-1",
    )
    with pytest.raises(PathValidationError, match="Step ordering violation"):
        validate_reproduction_path(path)


def test_validate_reproduction_path_empty_seed():
    """Verify empty seed URL raises PathValidationError."""
    path = ReproductionPath(
        path_id="path-empty-seed",
        trajectory_id=uuid4(),
        classification_id="class-1",
        difference_id="diff-1",
        seed_url="",
        steps=[],
        path_signature="sig-1",
    )
    with pytest.raises(PathValidationError, match="non-empty seed_url"):
        validate_reproduction_path(path)
