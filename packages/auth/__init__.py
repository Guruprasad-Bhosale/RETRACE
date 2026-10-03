"""RETRACE Multi-Tenant Authentication and RBAC Package."""

from packages.auth.api_keys import generate_api_key, hash_secret, verify_api_key_secret
from packages.auth.dependencies import get_current_principal, require_permission
from packages.auth.models import (
    Action,
    ApiKey,
    Organization,
    Principal,
    Role,
    User,
    Workspace,
    WorkspaceMembership,
)
from packages.auth.rbac import AuthorizationError, authorize, enforce_authorization

__all__ = [
    "Action",
    "ApiKey",
    "AuthorizationError",
    "Organization",
    "Principal",
    "Role",
    "User",
    "Workspace",
    "WorkspaceMembership",
    "authorize",
    "enforce_authorization",
    "generate_api_key",
    "get_current_principal",
    "hash_secret",
    "require_permission",
    "verify_api_key_secret",
]
