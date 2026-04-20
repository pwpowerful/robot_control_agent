from __future__ import annotations

from datetime import datetime

from pydantic import Field

from robot_control_backend.api_server.contracts import ApiPayloadModel


class AuthApiModel(ApiPayloadModel):
    """Base model for auth API contracts."""


class LoginRequest(AuthApiModel):
    """Credential payload for a login request."""

    username: str = Field(description="Bootstrap username for the requested role.")
    password: str = Field(description="Plain-text password checked against the configured bootstrap secret.")


class AuthenticatedUserResponse(AuthApiModel):
    """Logged-in user summary returned to the console."""

    user_id: str = Field(description="Stable user identifier.")
    username: str = Field(description="Unique login name.")
    display_name: str = Field(description="Display name shown in the console.")
    role_codes: list[str] = Field(description="Assigned RBAC role codes.")
    permission_codes: list[str] = Field(description="Effective permissions granted by the role set.")
    page_access: list[str] = Field(description="Allowed console page areas for the current user.")


class ActiveSessionResponse(AuthApiModel):
    """Session summary returned after login or session refresh."""

    session_id: str = Field(description="Server-side session identifier.")
    session_backend: str = Field(description="Current session backend implementation.")
    issued_at: datetime = Field(description="Session issuance timestamp.")
    last_seen_at: datetime = Field(description="Last activity timestamp known to the server.")
    expires_at: datetime = Field(description="Session expiration timestamp.")
    user: AuthenticatedUserResponse = Field(description="Authenticated user summary.")


class LogoutResponse(AuthApiModel):
    """Logout result returned after cookie revocation."""

    status: str = Field(description="Stable logout status.")


class AccessCheckResponse(AuthApiModel):
    """Structured response used by Step 09 permission boundary tests."""

    scope: str = Field(description="Protected business scope that was checked.")
    required_permission: str = Field(description="Permission required to reach the scope.")
    allowed: bool = Field(description="Whether access was granted.")
    message: str = Field(description="Human-readable access result.")


class RolePermissionMatrixEntry(AuthApiModel):
    """Single role definition rendered as API output and docs input."""

    role_code: str = Field(description="Stable role code.")
    display_name: str = Field(description="Display name of the role.")
    description: str = Field(description="Human-readable role summary.")
    permission_codes: list[str] = Field(description="Effective permissions granted by the role.")
    page_access: list[str] = Field(description="Allowed page areas for the role.")
    interface_groups: list[str] = Field(description="Business interface groups the role may use.")
    data_access_scope: list[str] = Field(description="Data operations explicitly granted to the role.")
    audit_access_scope: str = Field(description="Audit access boundary such as none or full.")


class PermissionMatrixResponse(AuthApiModel):
    """Top-level RBAC matrix response exposed for console bootstrapping and docs verification."""

    roles: list[RolePermissionMatrixEntry] = Field(description="All supported role definitions for the current MVP.")
