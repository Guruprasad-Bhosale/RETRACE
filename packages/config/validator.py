"""RETRACE Production Configuration Validator.

Provides pre-flight configuration audits that verify database, cache, storage,
and security settings without leaking sensitive credential values.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from packages.config.settings import Settings, get_settings


class CheckStatus(StrEnum):
    """Status of an individual configuration check."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class ConfigCheckResult:
    """Individual configuration audit result."""

    category: str
    item: str
    status: CheckStatus
    message: str
    masked_value: str | None = None


def mask_sensitive_string(val: str | None) -> str:
    """Mask credentials while exposing prefix/scheme for verification."""
    if not val:
        return "<not set>"
    if "://" in val:
        scheme, rest = val.split("://", 1)
        if "@" in rest:
            creds, host_part = rest.split("@", 1)
            return f"{scheme}://***:***@{host_part}"
        return f"{scheme}://{rest}"
    if len(val) <= 6:
        return "***"
    return f"{val[:3]}...{val[-3:]}"


class ConfigurationValidator:
    """Audits settings for environment readiness and security compliance."""

    @classmethod
    def audit(cls, settings: Settings | None = None) -> list[ConfigCheckResult]:
        """Perform full validation audit of application settings."""
        cfg = settings or get_settings()
        results: list[ConfigCheckResult] = []

        # 1. Environment & Debug
        if cfg.ENVIRONMENT == "production":
            if cfg.DEBUG:
                results.append(
                    ConfigCheckResult(
                        category="Environment",
                        item="DEBUG",
                        status=CheckStatus.FAIL,
                        message="DEBUG is enabled in production environment.",
                    )
                )
            else:
                results.append(
                    ConfigCheckResult(
                        category="Environment",
                        item="DEBUG",
                        status=CheckStatus.PASS,
                        message="DEBUG mode is correctly disabled.",
                    )
                )
        else:
            results.append(
                ConfigCheckResult(
                    category="Environment",
                    item="ENVIRONMENT",
                    status=CheckStatus.PASS,
                    message=f"Running in '{cfg.ENVIRONMENT}' mode.",
                )
            )

        # 2. Secret Key
        if "retrace-dev-secret-key" in cfg.SECRET_KEY:
            if cfg.ENVIRONMENT == "production":
                results.append(
                    ConfigCheckResult(
                        category="Security",
                        item="SECRET_KEY",
                        status=CheckStatus.FAIL,
                        message="Default insecure development SECRET_KEY detected in production.",
                    )
                )
            else:
                results.append(
                    ConfigCheckResult(
                        category="Security",
                        item="SECRET_KEY",
                        status=CheckStatus.WARN,
                        message="Using default development SECRET_KEY.",
                        masked_value=mask_sensitive_string(cfg.SECRET_KEY),
                    )
                )
        else:
            results.append(
                ConfigCheckResult(
                    category="Security",
                    item="SECRET_KEY",
                    status=CheckStatus.PASS,
                    message="Custom SECRET_KEY configured.",
                    masked_value=mask_sensitive_string(cfg.SECRET_KEY),
                )
            )

        # 3. Database URL
        db_masked = mask_sensitive_string(cfg.DATABASE_URL)
        if "localhost" in cfg.DATABASE_URL or "127.0.0.1" in cfg.DATABASE_URL:
            if cfg.ENVIRONMENT == "production":
                results.append(
                    ConfigCheckResult(
                        category="Database",
                        item="DATABASE_URL",
                        status=CheckStatus.FAIL,
                        message="DATABASE_URL must not point to localhost in production.",
                        masked_value=db_masked,
                    )
                )
            else:
                results.append(
                    ConfigCheckResult(
                        category="Database",
                        item="DATABASE_URL",
                        status=CheckStatus.PASS,
                        message="Local database configured.",
                        masked_value=db_masked,
                    )
                )
        else:
            results.append(
                ConfigCheckResult(
                    category="Database",
                    item="DATABASE_URL",
                    status=CheckStatus.PASS,
                    message="Remote/managed database endpoint configured.",
                    masked_value=db_masked,
                )
            )

        # 4. Redis URL
        redis_masked = mask_sensitive_string(cfg.REDIS_URL)
        if "localhost" in cfg.REDIS_URL or "127.0.0.1" in cfg.REDIS_URL:
            if cfg.ENVIRONMENT == "production":
                results.append(
                    ConfigCheckResult(
                        category="Redis",
                        item="REDIS_URL",
                        status=CheckStatus.FAIL,
                        message="REDIS_URL must not point to localhost in production.",
                        masked_value=redis_masked,
                    )
                )
            else:
                results.append(
                    ConfigCheckResult(
                        category="Redis",
                        item="REDIS_URL",
                        status=CheckStatus.PASS,
                        message="Local Redis endpoint configured.",
                        masked_value=redis_masked,
                    )
                )
        else:
            results.append(
                ConfigCheckResult(
                    category="Redis",
                    item="REDIS_URL",
                    status=CheckStatus.PASS,
                    message="Remote/managed Redis endpoint configured.",
                    masked_value=redis_masked,
                )
            )

        # 5. Storage Backend
        if cfg.STORAGE_BACKEND == "s3":
            results.append(
                ConfigCheckResult(
                    category="Storage",
                    item="STORAGE_BACKEND",
                    status=CheckStatus.PASS,
                    message=f"S3 artifact storage configured on bucket '{cfg.STORAGE_S3_BUCKET}'.",
                    masked_value=cfg.STORAGE_S3_BUCKET,
                )
            )
        elif cfg.ENVIRONMENT == "production":
            results.append(
                ConfigCheckResult(
                    category="Storage",
                    item="STORAGE_BACKEND",
                    status=CheckStatus.FAIL,
                    message="Local storage backend is disallowed in production (S3 required).",
                )
            )
        else:
            results.append(
                ConfigCheckResult(
                    category="Storage",
                    item="STORAGE_BACKEND",
                    status=CheckStatus.PASS,
                    message=f"Local disk storage configured at '{cfg.STORAGE_LOCAL_DIR}'.",
                )
            )

        # 6. CORS Origins
        if "*" in cfg.CORS_ORIGINS:
            if cfg.ENVIRONMENT == "production":
                results.append(
                    ConfigCheckResult(
                        category="Security",
                        item="CORS_ORIGINS",
                        status=CheckStatus.FAIL,
                        message="Wildcard CORS origins disallowed in production.",
                    )
                )
            else:
                results.append(
                    ConfigCheckResult(
                        category="Security",
                        item="CORS_ORIGINS",
                        status=CheckStatus.WARN,
                        message="Wildcard CORS origins enabled for development.",
                    )
                )
        else:
            results.append(
                ConfigCheckResult(
                    category="Security",
                    item="CORS_ORIGINS",
                    status=CheckStatus.PASS,
                    message=f"{len(cfg.CORS_ORIGINS)} explicit CORS origin(s) configured.",
                )
            )

        # 7. Worker Resource & Sandbox Controls
        if cfg.WORKER_BROWSER_SANDBOX:
            results.append(
                ConfigCheckResult(
                    category="Worker",
                    item="BROWSER_SANDBOX",
                    status=CheckStatus.PASS,
                    message="Browser sandbox flags and navigation safety enabled.",
                )
            )
        else:
            results.append(
                ConfigCheckResult(
                    category="Worker",
                    item="BROWSER_SANDBOX",
                    status=CheckStatus.WARN,
                    message="Browser sandbox disabled.",
                )
            )

        return results

    @classmethod
    def print_audit_report(cls, settings: Settings | None = None) -> int:
        """Print formatted CLI audit report. Return 0 if valid, 1 if failures exist."""
        results = cls.audit(settings)
        cfg = settings or get_settings()

        print("\n" + "=" * 70)
        print(f"RETRACE Configuration Pre-flight Check -- [{cfg.ENVIRONMENT.upper()}]")
        print("=" * 70)

        has_failures = False
        for res in results:
            icon = "[PASS]" if res.status == CheckStatus.PASS else ("[WARN]" if res.status == CheckStatus.WARN else "[FAIL]")
            val_str = f" ({res.masked_value})" if res.masked_value else ""
            print(f"{icon:<7} {res.category:<12} | {res.item:<18} | {res.message}{val_str}")
            if res.status == CheckStatus.FAIL:
                has_failures = True

        print("=" * 70)
        if has_failures:
            print("RESULT: Configuration check FAILED with errors.")
            print("=" * 70 + "\n")
            return 1
        print("RESULT: Configuration check PASSED successfully.")
        print("=" * 70 + "\n")
        return 0


def main() -> None:
    """CLI Entrypoint."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="RETRACE Configuration Validator")
    parser.add_argument(
        "--environment",
        choices=["development", "test", "testing", "staging", "production"],
        default=None,
        help="Simulate specific environment configuration check",
    )
    args = parser.parse_args()

    cfg = get_settings()
    if args.environment:
        # Create shallow copy with overridden environment for validation
        raw_dict: dict[str, Any] = cfg.model_dump()
        raw_dict["ENVIRONMENT"] = args.environment
        if args.environment == "production" and "retrace-dev-secret-key" in raw_dict["SECRET_KEY"]:
            # Let's test what happens when standard settings are passed
            pass
        try:
            cfg = Settings(**raw_dict)
        except Exception as e:
            print(f"[FAIL] Configuration error initializing for {args.environment}:\n{e}")
            sys.exit(1)

    exit_code = ConfigurationValidator.print_audit_report(cfg)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
