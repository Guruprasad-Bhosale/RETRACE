"""Version A/B Exploration and Alignment Runner Module.

Provides an orchestration facade to explore Version A (baseline) and Version B (target)
using Phase 4 AutonomousExplorer, and generate behavioral trajectory alignment using TrajectoryAligner.
"""

from uuid import UUID, uuid4

from apps.worker.alignment.config import AlignmentConfig
from apps.worker.alignment.models import AlignmentResult
from apps.worker.alignment.trajectory_alignment import TrajectoryAligner
from apps.worker.browser.manager import BrowserManager
from apps.worker.exploration.config import ExplorationConfig
from apps.worker.exploration.explorer import AutonomousExplorer
from packages.storage.base import ArtifactStorage


class ABAnalysisRunner:
    """Orchestrates independent Phase 4 exploration on Version A & Version B and aligns results."""

    def __init__(
        self,
        browser_manager: BrowserManager,
        artifact_storage: ArtifactStorage,
        alignment_config: AlignmentConfig | None = None,
        exploration_config: ExplorationConfig | None = None,
    ) -> None:
        self.browser_manager = browser_manager
        self.artifact_storage = artifact_storage
        self.alignment_config = alignment_config or AlignmentConfig()
        self.exploration_config = exploration_config or ExplorationConfig()
        self.aligner = TrajectoryAligner(config=self.alignment_config)

    async def run_ab_alignment(
        self,
        analysis_id: UUID | None = None,
        seed_url_a: str | None = None,
        seed_url_b: str | None = None,
    ) -> AlignmentResult:
        """Run independent exploration against Version A and Version B, then align observed trajectories."""
        aid = analysis_id or uuid4()
        url_a = seed_url_a or self.alignment_config.version_a_base_url
        url_b = seed_url_b or self.alignment_config.version_b_base_url

        # Explore Version A (Baseline)
        explorer_a = AutonomousExplorer(
            browser_manager=self.browser_manager,
            storage=self.artifact_storage,
            config=self.exploration_config,
        )
        result_a = await explorer_a.explore(
            analysis_id=aid,
            version_id="version_a",
            seed_url=url_a,
        )

        # Explore Version B (Target)
        explorer_b = AutonomousExplorer(
            browser_manager=self.browser_manager,
            storage=self.artifact_storage,
            config=self.exploration_config,
        )
        result_b = await explorer_b.explore(
            analysis_id=aid,
            version_id="version_b",
            seed_url=url_b,
        )

        # Align exploration graphs
        return self.aligner.align(result_a=result_a, result_b=result_b)
