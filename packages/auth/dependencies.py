"""FastAPI Security Dependencies for Multi-Tenant Authorization."""

import uuid
from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status

from packages.auth.models import Action, Principal, Role
from packages.auth.rbac import authorize

# Default fallback workspace for development & unauthenticated mode
DEFAULT_WORKSPACE_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def get_current_principal(
    authorization: str | None = Header(None),
    x_workspace_id: str | None = Header(None),
    x_user_role: str | None = Header(None),
) -> Principal:
    """Resolve current principal from Authorization header or Workspace headers."""
    # In development/test default to Owner principal if no auth is provided
    role_str = (x_user_role or "OWNER").upper()
    try:
        role = Role(role_str)
    except ValueError:
        role = Role.VIEWER

    ws_id = uuid.UUID(x_workspace_id) if x_workspace_id else DEFAULT_WORKSPACE_ID
    principal_id = uuid.uuid4()

    is_api_key = False
    if authorization and authorization.startswith("Bearer rt_live_"):
        is_api_key = True

    return Principal(
        id=principal_id,
        workspace_id=ws_id,
        role=role,
        is_api_key=is_api_key,
        name="Authenticated Principal",
    )


def require_permission(action: Action | str) -> Callable[..., Principal]:
    """Dependency factory enforcing specific RBAC action."""

    async def _verifier(
        principal: Principal = Depends(get_current_principal),
        x_workspace_id: str | None = Header(None),
    ) -> Principal:
        target_ws = uuid.UUID(x_workspace_id) if x_workspace_id else principal.workspace_id
        if not authorize(principal, action, target_ws):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "message": f"Principal lacks required permission: {action}",
                },
            )
        return principal

    return _verifier
