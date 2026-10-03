"""Multi-Tenant Domain Entities, User Models, and RBAC Definitions for RETRACE.

Defines Organization, Workspace, User, Membership, API Key, and Principal domain entities
with explicit workspace isolation boundaries and role hierarchies.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class Role(StrEnum):
    """Workspace-level Role-Based Access Control roles."""

    OWNER = "OWNER"
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class Action(StrEnum):
    """Standardized action permissions for authorization."""

    WORKSPACE_MANAGE = "workspace:manage"
    MEMBERS_MANAGE = "members:manage"
    API_KEYS_MANAGE = "api_keys:manage"
    PROJECT_CREATE = "project:create"
    PROJECT_DELETE = "project:delete"
    ANALYSIS_EXECUTE = "analysis:execute"
    INVESTIGATION_VIEW = "investigation:view"
    ARTIFACT_VIEW = "artifact:view"


@dataclass
class Organization:
    """Tenant Organization entity."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = "Default Organization"
    slug: str = "default-org"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Workspace:
    """Tenant Workspace entity providing hard multi-tenant isolation boundary."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    organization_id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = "Default Workspace"
    slug: str = "default-workspace"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class User:
    """Platform User entity."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    email: str = "analyst@retrace.local"
    name: str = "Platform User"
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkspaceMembership:
    """Binds a user to a specific workspace with a designated role."""

    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: Role = Role.ANALYST
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ApiKey:
    """Workspace API key entity with hashed secret storage and prefix masking."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    workspace_id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = "CI/CD Deployment Key"
    key_prefix: str = "rt_live_"
    hashed_key: str = ""
    role: Role = Role.ANALYST
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        """Verify key has not been revoked or expired."""
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and datetime.now(UTC) > self.expires_at:
            return False
        return True

    @property
    def masked_key(self) -> str:
        """Safe non-sensitive presentation format."""
        return f"{self.key_prefix}••••••••"


@dataclass
class Principal:
    """Authenticated caller identity (User or API Key)."""

    id: uuid.UUID
    workspace_id: uuid.UUID
    role: Role
    is_api_key: bool = False
    name: str = "Anonymous"
    email: str | None = None
    organization_id: uuid.UUID | None = None
