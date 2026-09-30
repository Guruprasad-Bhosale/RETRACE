"""RETRACE Autonomous Exploration Engine Package."""

from apps.worker.exploration.backtracking import Backtracker
from apps.worker.exploration.candidate import CandidateAction, CandidateGenerator
from apps.worker.exploration.config import ExplorationConfig
from apps.worker.exploration.coverage import CoverageMetrics, CoverageTracker
from apps.worker.exploration.diagnostics import ExplorationDiagnosticsFormatter, ExplorationResult
from apps.worker.exploration.errors import (
    BacktrackingFailedError,
    ExcessiveFailuresError,
    ExplorationError,
    ExplorationTimeoutError,
    FrontierExhaustedError,
    RecoveryMismatchError,
    SafetyViolationError,
)
from apps.worker.exploration.explorer import AutonomousExplorer
from apps.worker.exploration.frontier import ExplorationFrontier, FrontierItem
from apps.worker.exploration.guards import ActionSafetyGuard, URLSafetyGuard
from apps.worker.exploration.route_tracker import RouteTracker
from apps.worker.exploration.state import ExplorationGraph, ExplorationState
from apps.worker.exploration.state_identity import StateIdentity, StateIdentityCalculator
from apps.worker.exploration.transition import ExplorationTransition, compute_transition_id

__all__ = [
    "ActionSafetyGuard",
    "AutonomousExplorer",
    "Backtracker",
    "BacktrackingFailedError",
    "CandidateAction",
    "CandidateGenerator",
    "CoverageMetrics",
    "CoverageTracker",
    "ExcessiveFailuresError",
    "ExplorationConfig",
    "ExplorationDiagnosticsFormatter",
    "ExplorationError",
    "ExplorationFrontier",
    "ExplorationGraph",
    "ExplorationResult",
    "ExplorationState",
    "ExplorationTimeoutError",
    "FrontierExhaustedError",
    "FrontierItem",
    "RecoveryMismatchError",
    "RouteTracker",
    "SafetyViolationError",
    "StateIdentity",
    "StateIdentityCalculator",
    "ExplorationTransition",
    "URLSafetyGuard",
    "compute_transition_id",
]
