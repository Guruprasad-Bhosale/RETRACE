"""Centralized Role-Based Access Control (RBAC) and Tenant Isolation Layer.

Enforces workspace boundary isolation and validates role permissions before
allowing operations on projects, analyses, investigations, and artifacts.
"""

import uuid
from typing import Any

from packages.auth.models import Action, Principal, Role
from packages.logging.logger import LogEvents, get_logger

logger = get_logger(__name__)

# Explicit Role Permission Matrix
ROLE_PERMISSIONS: dict[Role, set[Action]] = {
    Role.OWNER: {
        Action.WORKSPACE_MANAGE,
        Action.MEMBERS_MANAGE,
        Action.API_KEYS_MANAGE,
        Action.PROJECT_CREATE,
        Action.PROJECT_DELETE,
        Action.ANALYSIS_EXECUTE,
        Action.INVESTIGATION_VIEW,
        Action.ARTIFACT_VIEW,
    },
    Role.ADMIN: {
        Action.MEMBERS_MANAGE,
        Action.PROJECT_CREATE,
        Action.PROJECT_DELETE,
        Action.ANALYSIS_EXECUTE,
        Action.INVESTIGATION_VIEW,
        Action.ARTIFACT_VIEW,
    },
    Role.ANALYST: {
        Action.PROJECT_CREATE,
        Action.ANALYSIS_EXECUTE,
        Action.INVESTIGATION_VIEW,
        Action.ARTIFACT_VIEW,
    },
    Role.VIEWER: {
        Action.INVESTIGATION_VIEW,
        Action.ARTIFACT_VIEW,
    },
}


class AuthorizationError(Exception):
    """Raised when access is denied or tenant isolation is violated."""

    def __init__(self, message: str, code: str = "FORBIDDEN") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def authorize(
    principal: Principal | None,
    action: Action | str,
    resource_workspace_id: uuid.UUID | str | None = None,
    resource_context: dict[str, Any] | None = None,
) -> bool:
    """Authorize a principal to perform an action against a workspace resource.

    CRITICAL INVARIANTS:
    1. Unauthenticated callers are rejected immediately.
    2. Cross-tenant access (where principal.workspace_id != resource_workspace_id)
       is strictly rejected with zero leakage.
    3. The caller's role must possess the required Action permission.
    """
    if principal is None:
        logger.warning(
            "Authorization denied: unauthenticated caller",
            event_type=LogEvents.AUTHORIZATION_DENIED,
            action=str(action),
        )
        return False

    # Standardize action enum
    try:
        action_enum = Action(action) if isinstance(action, str) else action
    except ValueError:
        logger.warning("Authorization denied: invalid action", action=str(action))
        return False

    # Workspace Boundary / Tenant Isolation Check
    if resource_workspace_id is not None:
        target_ws = (
            uuid.UUID(str(resource_workspace_id))
            if isinstance(resource_workspace_id, str)
            else resource_workspace_id
        )
        if principal.workspace_id != target_ws:
            logger.warning(
                "Cross-tenant access attempted and blocked",
                event_type=LogEvents.AUTHORIZATION_DENIED,
                caller_workspace_id=str(principal.workspace_id),
                target_workspace_id=str(target_ws),
                caller_id=str(principal.id),
                action=action_enum.value,
            )
            return False

    # Role Permission Check
    allowed_actions = ROLE_PERMISSIONS.get(principal.role, set())
    if action_enum not in allowed_actions:
        logger.warning(
            "Permission denied for role",
            event_type=LogEvents.AUTHORIZATION_DENIED,
            role=principal.role.value,
            action=action_enum.value,
            caller_id=str(principal.id),
        )
        return False

    return True


def enforce_authorization(
    principal: Principal | None,
    action: Action | str,
    resource_workspace_id: uuid.UUID | str | None = None,
) -> None:
    """Authorize or raise AuthorizationError exception."""
    if not authorize(principal, action, resource_workspace_id):
        raise AuthorizationError(
            f"Unauthorized: Caller lacks permission '{action}' for target workspace.",
            code="FORBIDDEN",
        )
