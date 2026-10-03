# RETRACE Database Migration Strategy & Operations

## 1. Overview

RETRACE uses **Alembic** for deterministic, version-controlled schema migrations on PostgreSQL.

## 2. Migration Guidelines

1. **Deterministic & Forward-Only**: Every migration script must be idempotent and support clean upgrades (`alembic upgrade head`) and downgrades (`alembic downgrade -1`).
2. **Expand / Contract Pattern**:
   - **Step 1 (Expand)**: Add new columns/tables with nullable or default values.
   - **Step 2 (Deploy)**: Deploy application code writing to new structures.
   - **Step 3 (Contract)**: Remove deprecated columns in a subsequent release.
3. **No Lock Contention**: Avoid long table locks on high-traffic tables.

## 3. Migration Commands

```bash
# Generate new migration from SQLAlchemy model changes
alembic revision --autogenerate -m "description_of_change"

# Verify migration scripts (single head verification)
python -m packages.db.migrations --check

# Apply migrations
python -m packages.db.migrations --apply

# Rollback one migration step
python -m packages.db.migrations --rollback
```
