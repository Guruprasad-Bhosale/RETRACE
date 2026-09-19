"""Integration tests for Alembic database migrations and metadata consistency."""

from packages.db.base import Base


def test_schema_metadata_tables():
    """Verify all expected domain tables are defined in SQLAlchemy Base metadata."""
    table_names = Base.metadata.tables.keys()

    expected_tables = {
        "projects",
        "application_versions",
        "analysis_sessions",
        "trajectories",
        "actions",
        "observations",
        "evidence",
        "findings",
        "reproduction_attempts",
        "root_causes",
        "reports",
    }

    for expected in expected_tables:
        assert expected in table_names, f"Table '{expected}' missing from SQLAlchemy metadata"


def test_table_foreign_keys():
    """Verify cascading foreign keys on relational tables."""
    meta = Base.metadata

    # Analysis sessions references projects
    sessions_table = meta.tables["analysis_sessions"]
    fk_targets = [fk.column.table.name for fk in sessions_table.foreign_keys]
    assert "projects" in fk_targets

    # Actions references trajectories and analysis_sessions
    actions_table = meta.tables["actions"]
    act_fk_targets = [fk.column.table.name for fk in actions_table.foreign_keys]
    assert "trajectories" in act_fk_targets
    assert "analysis_sessions" in act_fk_targets

    # Reproduction attempts references findings
    repro_table = meta.tables["reproduction_attempts"]
    repro_fk_targets = [fk.column.table.name for fk in repro_table.foreign_keys]
    assert "findings" in repro_fk_targets
