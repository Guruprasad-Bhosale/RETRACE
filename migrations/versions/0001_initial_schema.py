"""initial schema

Revision ID: 0001
Revises: None
Create Date: 2026-09-14 21:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create projects table
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_projects_name"), "projects", ["name"], unique=False)

    # Create analysis_sessions table
    op.create_table(
        "analysis_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column(
            "version_a_meta",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "version_b_meta",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"
        ),
        sa.Column("workflows_explored", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("regressions_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        op.f("ix_analysis_sessions_project_id"), "analysis_sessions", ["project_id"], unique=False
    )
    op.create_index(
        op.f("ix_analysis_sessions_status"), "analysis_sessions", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_analysis_sessions_status"), table_name="analysis_sessions")
    op.drop_index(op.f("ix_analysis_sessions_project_id"), table_name="analysis_sessions")
    op.drop_table("analysis_sessions")
    op.drop_index(op.f("ix_projects_name"), table_name="projects")
    op.drop_table("projects")
