"""Tenant Isolation, RBAC Permissions, and API Key Security Test Suite."""

import uuid
from datetime import UTC, datetime

import pytest

from packages.auth.api_keys import (
    API_KEY_PREFIX,
    generate_api_key,
    verify_api_key_secret,
)
from packages.auth.models import (
    Action,
    Organization,
    Principal,
    Role,
    Workspace,
)
from packages.auth.rbac import (
    AuthorizationError,
    authorize,
    enforce_authorization,
)


def test_organization_and_workspace_hierarchy() -> None:
    """Validate organization and workspace isolation models."""
    org = Organization(name="Acme Corp", slug="acme-corp")
    ws_prod = Workspace(organization_id=org.id, name="Production", slug="prod")
    ws_staging = Workspace(organization_id=org.id, name="Staging", slug="staging")

    assert ws_prod.organization_id == org.id
    assert ws_staging.organization_id == org.id
    assert ws_prod.id != ws_staging.id


def test_api_key_generation_and_hashing() -> None:
    """Validate secure API key generation, prefixing, masking, and hashing."""
    ws_id = uuid.uuid4()
    raw_key, api_key_model = generate_api_key(
        workspace_id=ws_id,
        name="CI Key",
        role=Role.ANALYST,
        expires_in_days=30,
    )

    assert raw_key.startswith(API_KEY_PREFIX)
    assert len(raw_key) > 30
    assert api_key_model.hashed_key != raw_key
    assert api_key_model.masked_key == "rt_live_••••••••"
    assert api_key_model.is_active is True

    # Verification
    assert verify_api_key_secret(raw_key, api_key_model.hashed_key) is True
    assert verify_api_key_secret("rt_live_wrong_token", api_key_model.hashed_key) is False


def test_api_key_revocation_and_expiration() -> None:
    """Validate revoked or expired API keys are marked inactive."""
    ws_id = uuid.uuid4()
    _, key_active = generate_api_key(workspace_id=ws_id)
    assert key_active.is_active is True

    # Revoked key
    key_active.revoked_at = datetime.now(UTC)
    assert key_active.is_active is False

    # Expired key
    _, key_expired = generate_api_key(
        workspace_id=ws_id,
        expires_in_days=-1,  # in past
    )
    assert key_expired.is_active is False


def test_rbac_permission_matrix() -> None:
    """Validate role permissions strictly follow least privilege."""
    ws_id = uuid.uuid4()

    owner = Principal(id=uuid.uuid4(), workspace_id=ws_id, role=Role.OWNER)
    admin = Principal(id=uuid.uuid4(), workspace_id=ws_id, role=Role.ADMIN)
    analyst = Principal(id=uuid.uuid4(), workspace_id=ws_id, role=Role.ANALYST)
    viewer = Principal(id=uuid.uuid4(), workspace_id=ws_id, role=Role.VIEWER)

    # Workspace Management: Owner only
    assert authorize(owner, Action.WORKSPACE_MANAGE, ws_id) is True
    assert authorize(admin, Action.WORKSPACE_MANAGE, ws_id) is False
    assert authorize(analyst, Action.WORKSPACE_MANAGE, ws_id) is False
    assert authorize(viewer, Action.WORKSPACE_MANAGE, ws_id) is False

    # API Keys: Owner only
    assert authorize(owner, Action.API_KEYS_MANAGE, ws_id) is True
    assert authorize(admin, Action.API_KEYS_MANAGE, ws_id) is False
    assert authorize(analyst, Action.API_KEYS_MANAGE, ws_id) is False

    # Project Delete: Owner and Admin
    assert authorize(owner, Action.PROJECT_DELETE, ws_id) is True
    assert authorize(admin, Action.PROJECT_DELETE, ws_id) is True
    assert authorize(analyst, Action.PROJECT_DELETE, ws_id) is False
    assert authorize(viewer, Action.PROJECT_DELETE, ws_id) is False

    # Analysis Execute: Owner, Admin, Analyst
    assert authorize(owner, Action.ANALYSIS_EXECUTE, ws_id) is True
    assert authorize(admin, Action.ANALYSIS_EXECUTE, ws_id) is True
    assert authorize(analyst, Action.ANALYSIS_EXECUTE, ws_id) is True
    assert authorize(viewer, Action.ANALYSIS_EXECUTE, ws_id) is False

    # Investigation View: All roles
    assert authorize(owner, Action.INVESTIGATION_VIEW, ws_id) is True
    assert authorize(admin, Action.INVESTIGATION_VIEW, ws_id) is True
    assert authorize(analyst, Action.INVESTIGATION_VIEW, ws_id) is True
    assert authorize(viewer, Action.INVESTIGATION_VIEW, ws_id) is True


def test_cross_tenant_isolation_enforcement() -> None:
    """CRITICAL SECURITY CHECK: Ensure Tenant A cannot access Tenant B resources under any role."""
    ws_tenant_a = uuid.uuid4()
    ws_tenant_b = uuid.uuid4()

    # Even an OWNER of Tenant A must NEVER access Tenant B
    tenant_a_owner = Principal(id=uuid.uuid4(), workspace_id=ws_tenant_a, role=Role.OWNER)

    # Cross-tenant read attempt
    assert authorize(tenant_a_owner, Action.INVESTIGATION_VIEW, ws_tenant_b) is False
    # Cross-tenant execution attempt
    assert authorize(tenant_a_owner, Action.ANALYSIS_EXECUTE, ws_tenant_b) is False
    # Cross-tenant delete attempt
    assert authorize(tenant_a_owner, Action.PROJECT_DELETE, ws_tenant_b) is False

    with pytest.raises(AuthorizationError):
        enforce_authorization(tenant_a_owner, Action.ANALYSIS_EXECUTE, ws_tenant_b)


def test_unauthenticated_authorization_rejection() -> None:
    """Ensure None principal is always denied."""
    assert authorize(None, Action.INVESTIGATION_VIEW, uuid.uuid4()) is False
    with pytest.raises(AuthorizationError):
        enforce_authorization(None, Action.INVESTIGATION_VIEW, uuid.uuid4())
