"""harden domain and persistence

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-14 22:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create application_versions table
    op.create_table(
        "application_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=False),
        sa.Column("git_repo_url", sa.String(length=512), nullable=True),
        sa.Column("git_commit_hash", sa.String(length=64), nullable=True),
        sa.Column("branch", sa.String(length=128), nullable=True),
        sa.Column("build_id", sa.String(length=128), nullable=True),
        sa.Column(
            "environment_variables",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        op.f("ix_application_versions_project_id"),
        "application_versions",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_application_versions_name"), "application_versions", ["name"], unique=False
    )
    op.create_index(
        op.f("ix_application_versions_git_commit_hash"),
        "application_versions",
        ["git_commit_hash"],
        unique=False,
    )

    # 2. Add version and version_ids columns to analysis_sessions
    op.add_column(
        "analysis_sessions", sa.Column("version", sa.Integer(), nullable=False, server_default="1")
    )
    op.add_column(
        "analysis_sessions", sa.Column("version_a_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        "analysis_sessions", sa.Column("version_b_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        "fk_analysis_sessions_version_a_id",
        "analysis_sessions",
        "application_versions",
        ["version_a_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_analysis_sessions_version_b_id",
        "analysis_sessions",
        "application_versions",
        ["version_b_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 3. Create trajectories table
    op.create_table(
        "trajectories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "name",
            sa.String(length=128),
            nullable=False,
            server_default="Main Exploration Trajectory",
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("step_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_trajectories_session_id"), "trajectories", ["session_id"], unique=False
    )
    op.create_index(
        op.f("ix_trajectories_version_id"), "trajectories", ["version_id"], unique=False
    )

    # 4. Create actions table
    op.create_table(
        "actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "trajectory_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("trajectories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(length=32), nullable=False),
        sa.Column("selector", sa.Text(), nullable=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("coordinates", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("prior_observation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resulting_observation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_actions_session_id"), "actions", ["session_id"], unique=False)
    op.create_index(op.f("ix_actions_trajectory_id"), "actions", ["trajectory_id"], unique=False)
    op.create_index(op.f("ix_actions_step_index"), "actions", ["step_index"], unique=False)

    # 5. Create observations table
    op.create_table(
        "observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "trajectory_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("trajectories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("page_title", sa.String(length=256), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("dom_hash", sa.String(length=64), nullable=True),
        sa.Column("a11y_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "state_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "artifacts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "provenance",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("prior_observation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("caused_by_action_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        op.f("ix_observations_session_id"), "observations", ["session_id"], unique=False
    )
    op.create_index(
        op.f("ix_observations_trajectory_id"), "observations", ["trajectory_id"], unique=False
    )
    op.create_index(
        op.f("ix_observations_step_index"), "observations", ["step_index"], unique=False
    )

    # 6. Create findings table
    op.create_table(
        "findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "workflow_path",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="candidate"),
        sa.Column(
            "evidence_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_findings_session_id"), "findings", ["session_id"], unique=False)
    op.create_index(op.f("ix_findings_category"), "findings", ["category"], unique=False)
    op.create_index(op.f("ix_findings_severity"), "findings", ["severity"], unique=False)
    op.create_index(op.f("ix_findings_status"), "findings", ["status"], unique=False)

    # 7. Create evidence table
    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("trajectory_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("observation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "finding_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("findings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column(
            "artifacts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "provenance",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_evidence_session_id"), "evidence", ["session_id"], unique=False)
    op.create_index(op.f("ix_evidence_finding_id"), "evidence", ["finding_id"], unique=False)
    op.create_index(op.f("ix_evidence_evidence_type"), "evidence", ["evidence_type"], unique=False)

    # 8. Create reproduction_attempts table
    op.create_table(
        "reproduction_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "finding_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("findings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column(
            "framework", sa.String(length=32), nullable=False, server_default="playwright_python"
        ),
        sa.Column("script_code", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="skipped"),
        sa.Column("execution_output", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "artifacts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_reproduction_attempts_finding_id"),
        "reproduction_attempts",
        ["finding_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reproduction_attempts_session_id"),
        "reproduction_attempts",
        ["session_id"],
        unique=False,
    )

    # 9. Create root_causes table
    op.create_table(
        "root_causes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "finding_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("findings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "hypothesis_type", sa.String(length=32), nullable=False, server_default="hypothesis"
        ),
        sa.Column("commit_hash", sa.String(length=64), nullable=True),
        sa.Column("file_path", sa.String(length=512), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.Column("diff_chunk", sa.Text(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "affected_components",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "supporting_evidence_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_root_causes_finding_id"), "root_causes", ["finding_id"], unique=False)
    op.create_index(op.f("ix_root_causes_session_id"), "root_causes", ["session_id"], unique=False)

    # 10. Create reports table
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "stats", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_reports_session_id"), "reports", ["session_id"], unique=True)


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("root_causes")
    op.drop_table("reproduction_attempts")
    op.drop_table("evidence")
    op.drop_table("findings")
    op.drop_table("observations")
    op.drop_table("actions")
    op.drop_table("trajectories")
    op.drop_constraint("fk_analysis_sessions_version_b_id", "analysis_sessions", type_="foreignkey")
    op.drop_constraint("fk_analysis_sessions_version_a_id", "analysis_sessions", type_="foreignkey")
    op.drop_column("analysis_sessions", "version_b_id")
    op.drop_column("analysis_sessions", "version_a_id")
    op.drop_column("analysis_sessions", "version")
    op.drop_table("application_versions")
