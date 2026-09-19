"""SQLAlchemy ORM Models for RETRACE Core Entities.

Implements relational mapping with foreign keys, cascading deletes, index strategies,
and dialect-agnostic JSONB/GUID representations without storing binary blobs.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import GUID, Base, JSONBType, TimestampMixin, UUIDPrimaryKeyMixin


class ProjectModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """SQLAlchemy model representing a Project."""

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    versions: Mapped[list["ApplicationVersionModel"]] = relationship(
        "ApplicationVersionModel", back_populates="project", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["AnalysisSessionModel"]] = relationship(
        "AnalysisSessionModel", back_populates="project", cascade="all, delete-orphan"
    )


class ApplicationVersionModel(Base, UUIDPrimaryKeyMixin):
    """SQLAlchemy model representing an Application Version under test."""

    __tablename__ = "application_versions"

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)
    git_repo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    git_commit_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    branch: Mapped[str | None] = mapped_column(String(128), nullable=True)
    build_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    environment_variables: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    project: Mapped[ProjectModel | None] = relationship("ProjectModel", back_populates="versions")


class AnalysisSessionModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """SQLAlchemy model representing an Analysis Session."""

    __tablename__ = "analysis_sessions"

    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_a_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("application_versions.id", ondelete="SET NULL"), nullable=True
    )
    version_b_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("application_versions.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # Optimistic Locking
    version_a_meta: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    version_b_meta: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    config: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    workflows_explored: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    regressions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[ProjectModel] = relationship("ProjectModel", back_populates="sessions")
    trajectories: Mapped[list["TrajectoryModel"]] = relationship(
        "TrajectoryModel", back_populates="session", cascade="all, delete-orphan"
    )
    findings: Mapped[list["FindingModel"]] = relationship(
        "FindingModel", back_populates="session", cascade="all, delete-orphan"
    )
    report: Mapped["ReportModel | None"] = relationship(
        "ReportModel", back_populates="session", uselist=False, cascade="all, delete-orphan"
    )


class TrajectoryModel(Base, UUIDPrimaryKeyMixin):
    """SQLAlchemy model representing an ordered exploration trajectory."""

    __tablename__ = "trajectories"

    session_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_id: Mapped[uuid.UUID] = mapped_column(GUID, nullable=False, index=True)
    name: Mapped[str] = mapped_column(
        String(128), default="Main Exploration Trajectory", nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    step_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped[AnalysisSessionModel] = relationship(
        "AnalysisSessionModel", back_populates="trajectories"
    )
    actions: Mapped[list["ActionModel"]] = relationship(
        "ActionModel", back_populates="trajectory", cascade="all, delete-orphan"
    )
    observations: Mapped[list["ObservationModel"]] = relationship(
        "ObservationModel", back_populates="trajectory", cascade="all, delete-orphan"
    )


class ActionModel(Base, UUIDPrimaryKeyMixin):
    """SQLAlchemy model representing a sequence-aware browser interaction."""

    __tablename__ = "actions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_id: Mapped[uuid.UUID] = mapped_column(GUID, nullable=False, index=True)
    trajectory_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("trajectories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    selector: Mapped[str | None] = mapped_column(Text, nullable=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    coordinates: Mapped[dict | None] = mapped_column(JSONBType, nullable=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    prior_observation_id: Mapped[uuid.UUID | None] = mapped_column(GUID, nullable=True)
    resulting_observation_id: Mapped[uuid.UUID | None] = mapped_column(GUID, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    trajectory: Mapped[TrajectoryModel] = relationship("TrajectoryModel", back_populates="actions")


class ObservationModel(Base, UUIDPrimaryKeyMixin):
    """SQLAlchemy model representing a rich, sequence-aware state snapshot in an action trajectory."""

    __tablename__ = "observations"

    session_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_id: Mapped[uuid.UUID] = mapped_column(GUID, nullable=False, index=True)
    trajectory_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("trajectories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    page_title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dom_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    a11y_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state_snapshot: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    artifacts: Mapped[list] = mapped_column(JSONBType, default=list, nullable=False)
    provenance: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    prior_observation_id: Mapped[uuid.UUID | None] = mapped_column(GUID, nullable=True)
    caused_by_action_id: Mapped[uuid.UUID | None] = mapped_column(GUID, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    trajectory: Mapped[TrajectoryModel] = relationship(
        "TrajectoryModel", back_populates="observations"
    )


class EvidenceModel(Base, UUIDPrimaryKeyMixin):
    """SQLAlchemy model representing deterministic evidence supporting or refuting findings."""

    __tablename__ = "evidence"

    session_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_id: Mapped[uuid.UUID | None] = mapped_column(GUID, nullable=True, index=True)
    trajectory_id: Mapped[uuid.UUID | None] = mapped_column(GUID, nullable=True)
    observation_id: Mapped[uuid.UUID | None] = mapped_column(GUID, nullable=True)
    finding_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID, ForeignKey("findings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    artifacts: Mapped[list] = mapped_column(JSONBType, default=list, nullable=False)
    provenance: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    finding: Mapped["FindingModel | None"] = relationship(
        "FindingModel", back_populates="evidence_items"
    )


class FindingModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """SQLAlchemy model representing a detected behavioral or contract regression."""

    __tablename__ = "findings"

    session_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    workflow_path: Mapped[list] = mapped_column(JSONBType, default=list, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="candidate", nullable=False, index=True)
    evidence_ids: Mapped[list] = mapped_column(JSONBType, default=list, nullable=False)

    session: Mapped[AnalysisSessionModel] = relationship(
        "AnalysisSessionModel", back_populates="findings"
    )
    reproductions: Mapped[list["ReproductionAttemptModel"]] = relationship(
        "ReproductionAttemptModel", back_populates="finding", cascade="all, delete-orphan"
    )
    root_causes: Mapped[list["RootCauseModel"]] = relationship(
        "RootCauseModel", back_populates="finding", cascade="all, delete-orphan"
    )
    evidence_items: Mapped[list[EvidenceModel]] = relationship(
        "EvidenceModel", back_populates="finding"
    )


class ReproductionAttemptModel(Base, UUIDPrimaryKeyMixin):
    """SQLAlchemy model representing an execution attempt to reproduce a candidate regression."""

    __tablename__ = "reproduction_attempts"

    finding_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    framework: Mapped[str] = mapped_column(String(32), default="playwright_python", nullable=False)
    script_code: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="skipped", nullable=False, index=True)
    execution_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    artifacts: Mapped[list] = mapped_column(JSONBType, default=list, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    finding: Mapped[FindingModel] = relationship("FindingModel", back_populates="reproductions")


class RootCauseModel(Base, UUIDPrimaryKeyMixin):
    """SQLAlchemy model representing a correlated root cause hypothesis."""

    __tablename__ = "root_causes"

    finding_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hypothesis_type: Mapped[str] = mapped_column(
        String(32), default="hypothesis", nullable=False, index=True
    )
    commit_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    diff_chunk: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    affected_components: Mapped[list] = mapped_column(JSONBType, default=list, nullable=False)
    supporting_evidence_ids: Mapped[list] = mapped_column(JSONBType, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    finding: Mapped[FindingModel] = relationship("FindingModel", back_populates="root_causes")


class ReportModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """SQLAlchemy model representing a derived engineering report."""

    __tablename__ = "reports"

    session_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    stats: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    metadata_json: Mapped[dict] = mapped_column(JSONBType, default=dict, nullable=False)

    session: Mapped[AnalysisSessionModel] = relationship(
        "AnalysisSessionModel", back_populates="report"
    )
