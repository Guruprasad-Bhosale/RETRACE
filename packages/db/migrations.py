"""RETRACE Database Migration Safety and Management Module.

Provides deterministic Alembic migration runners and pre-flight validation checks
for deployment pipelines.
"""

import argparse
import sys
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from packages.config.settings import get_settings
from packages.logging.logger import get_logger

logger = get_logger(__name__)


def get_alembic_config(ini_path: str = "alembic.ini") -> Config:
    """Load Alembic configuration with environment-driven DATABASE_SYNC_URL."""
    settings = get_settings()
    root_dir = Path(__file__).resolve().parent.parent.parent
    alembic_ini = root_dir / ini_path

    if not alembic_ini.exists():
        raise FileNotFoundError(f"Alembic configuration file not found at {alembic_ini}")

    config = Config(str(alembic_ini))
    config.set_main_option("sqlalchemy.url", settings.DATABASE_SYNC_URL)
    config.set_main_option("script_location", str(root_dir / "migrations"))
    return config


def check_migrations(config: Config | None = None) -> dict[str, Any]:
    """Check if all migration scripts are valid and up to date."""
    cfg = config or get_alembic_config()
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()

    logger.info("Checked Alembic migration heads", heads=heads)
    return {
        "status": "valid",
        "heads": heads,
        "multiple_heads": len(heads) > 1,
    }


def run_migrations(config: Config | None = None, revision: str = "head") -> None:
    """Apply database migrations deterministically up to target revision."""
    cfg = config or get_alembic_config()
    logger.info("Applying database migrations", target_revision=revision)
    command.upgrade(cfg, revision)
    logger.info("Database migrations applied successfully")


def rollback_migration(config: Config | None = None, revision: str = "-1") -> None:
    """Downgrade database migrations for rollback procedures."""
    cfg = config or get_alembic_config()
    logger.warning("Rolling back database migration", target_revision=revision)
    command.downgrade(cfg, revision)
    logger.info("Database rollback completed")


def main() -> None:
    """CLI Entrypoint for database migration management."""
    parser = argparse.ArgumentParser(description="RETRACE Database Migration Manager")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check migration state and verify single head",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply pending migrations to target database",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback last applied migration",
    )
    parser.add_argument(
        "--revision",
        default="head",
        help="Target revision (default: head)",
    )
    args = parser.parse_args()

    try:
        cfg = get_alembic_config()
        if args.check:
            res = check_migrations(cfg)
            if res.get("multiple_heads"):
                print(f"[FAIL] Multiple migration heads detected: {res['heads']}")
                sys.exit(1)
            print(f"[PASS] Migration check valid. Current head: {res['heads']}")
            sys.exit(0)

        if args.apply:
            run_migrations(cfg, revision=args.revision)
            print("[PASS] Migrations applied successfully.")
            sys.exit(0)

        if args.rollback:
            rollback_migration(cfg, revision=args.revision if args.revision != "head" else "-1")
            print("[PASS] Migration rollback completed.")
            sys.exit(0)

        parser.print_help()
    except Exception as e:
        print(f"[FAIL] Migration operation error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
