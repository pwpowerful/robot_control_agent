from __future__ import annotations

import hashlib
import secrets
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from robot_control_backend.auth.models import (
    ActiveSessionResponse,
    AuthenticatedUserResponse,
    PermissionMatrixResponse,
    RolePermissionMatrixEntry,
)
from robot_control_backend.auth.rbac import ROLE_DEFINITIONS, PageCode, PermissionCode, RoleCode, pages_for_roles, permissions_for_roles
from robot_control_backend.bootstrap.settings import Settings


class AuthenticationError(RuntimeError):
    """Raised when credentials or session state are invalid."""


@dataclass(frozen=True)
class StoredUser:
    """Bootstrap user definition used by the current auth implementation."""

    user_id: str
    username: str
    display_name: str
    role_codes: tuple[RoleCode, ...]


@dataclass
class StoredSession:
    """Server-side session state stored by the current process."""

    session_id: str
    user: StoredUser
    token_hash: str
    issued_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    client_ip: str | None
    user_agent: str | None
    revoked_at: datetime | None = None


class BootstrapAuthService:
    """In-process auth service using bootstrap credentials from settings."""

    session_backend_name = "in_memory_bootstrap"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = threading.RLock()
        self._users_by_username, self._passwords_by_username = self._build_bootstrap_users(settings)
        self._sessions_by_token_hash: dict[str, StoredSession] = {}

    def login(self, *, username: str, password: str, client_ip: str | None, user_agent: str | None) -> tuple[str, StoredSession]:
        """Authenticate a bootstrap user and create a server-side session."""
        normalized_username = username.strip()
        stored_user = self._users_by_username.get(normalized_username)
        expected_password = self._passwords_by_username.get(normalized_username)

        if stored_user is None or expected_password is None or not secrets.compare_digest(password, expected_password):
            raise AuthenticationError("Invalid username or password.")

        now = self._now()
        raw_token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(raw_token)
        session = StoredSession(
            session_id=str(uuid.uuid4()),
            user=stored_user,
            token_hash=token_hash,
            issued_at=now,
            last_seen_at=now,
            expires_at=now + timedelta(minutes=self._settings.auth.session_ttl_minutes),
            client_ip=client_ip,
            user_agent=user_agent,
        )

        with self._lock:
            self._sessions_by_token_hash[token_hash] = session

        return raw_token, session

    def get_active_session(self, raw_token: str | None) -> StoredSession | None:
        """Resolve a cookie token to an active, non-expired session."""
        if not raw_token:
            return None

        token_hash = self._hash_token(raw_token)
        now = self._now()
        with self._lock:
            session = self._sessions_by_token_hash.get(token_hash)
            if session is None:
                return None
            if session.revoked_at is not None or session.expires_at <= now:
                self._sessions_by_token_hash.pop(token_hash, None)
                return None

            session.last_seen_at = now
            return session

    def revoke_session(self, raw_token: str | None) -> None:
        """Revoke the current session if it exists."""
        if not raw_token:
            return

        token_hash = self._hash_token(raw_token)
        with self._lock:
            session = self._sessions_by_token_hash.get(token_hash)
            if session is None or session.revoked_at is not None:
                return
            session.revoked_at = self._now()

    def has_permission(self, session: StoredSession, permission: PermissionCode) -> bool:
        """Check whether the session grants a specific permission."""
        return permission in permissions_for_roles(session.user.role_codes)

    def build_session_response(self, session: StoredSession) -> ActiveSessionResponse:
        """Convert stored session state into an API response."""
        permission_codes = sorted(permission.value for permission in permissions_for_roles(session.user.role_codes))
        page_access = sorted(page.value for page in pages_for_roles(session.user.role_codes))
        return ActiveSessionResponse(
            session_id=session.session_id,
            session_backend=self.session_backend_name,
            issued_at=session.issued_at,
            last_seen_at=session.last_seen_at,
            expires_at=session.expires_at,
            user=AuthenticatedUserResponse(
                user_id=session.user.user_id,
                username=session.user.username,
                display_name=session.user.display_name,
                role_codes=[role.value for role in session.user.role_codes],
                permission_codes=permission_codes,
                page_access=page_access,
            ),
        )

    def permission_matrix(self) -> PermissionMatrixResponse:
        """Return the canonical RBAC matrix for the current MVP."""
        roles = []
        for role_code in (RoleCode.OPERATOR, RoleCode.ADMIN):
            definition = ROLE_DEFINITIONS[role_code]
            roles.append(
                RolePermissionMatrixEntry(
                    role_code=definition.role_code.value,
                    display_name=definition.display_name,
                    description=definition.description,
                    permission_codes=sorted(permission.value for permission in definition.permissions),
                    page_access=sorted(page.value for page in definition.page_access),
                    interface_groups=list(definition.interface_groups),
                    data_access_scope=list(definition.data_access_scope),
                    audit_access_scope=definition.audit_access_scope,
                )
            )
        return PermissionMatrixResponse(roles=roles)

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @staticmethod
    def _now() -> datetime:
        return datetime.now(tz=UTC)

    @staticmethod
    def _build_bootstrap_users(settings: Settings) -> tuple[dict[str, StoredUser], dict[str, str]]:
        admin_password = settings.auth_admin_password.get_secret_value() if settings.auth_admin_password else None
        operator_password = settings.auth_operator_password.get_secret_value() if settings.auth_operator_password else None
        if admin_password is None or operator_password is None:
            raise AuthenticationError("Bootstrap users require both admin and operator passwords to be configured.")

        users = {
            settings.auth_admin_username: StoredUser(
                user_id="user-admin",
                username=settings.auth_admin_username,
                display_name="管理员",
                role_codes=(RoleCode.ADMIN,),
            ),
            settings.auth_operator_username: StoredUser(
                user_id="user-operator",
                username=settings.auth_operator_username,
                display_name="操作员",
                role_codes=(RoleCode.OPERATOR,),
            ),
        }
        passwords = {
            settings.auth_admin_username: admin_password,
            settings.auth_operator_username: operator_password,
        }
        return users, passwords
