from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Request, status

from robot_control_backend.api_server.contracts import ApiErrorCode
from robot_control_backend.api_server.errors import ApiException
from robot_control_backend.auth.rbac import PermissionCode
from robot_control_backend.auth.service import BootstrapAuthService, StoredSession
from robot_control_backend.bootstrap.settings import Settings
from robot_control_backend.task_service.service import InMemoryTaskService


def get_app_settings(request: Request) -> Settings:
    """Resolve shared settings from the FastAPI application state."""
    return request.app.state.settings


def get_auth_service(request: Request) -> BootstrapAuthService:
    """Resolve the current auth service from application state."""
    return request.app.state.auth_service


def get_task_service(request: Request) -> InMemoryTaskService:
    """Resolve the current task service from application state."""
    return request.app.state.task_service


def require_authenticated_session(
    request: Request,
    settings: Settings = Depends(get_app_settings),
    auth_service: BootstrapAuthService = Depends(get_auth_service),
) -> StoredSession:
    """Require an authenticated session backed by the configured cookie."""
    session_token = request.cookies.get(settings.auth.session_cookie_name)
    session = auth_service.get_active_session(session_token)
    if session is None:
        raise ApiException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.AUTHENTICATION_REQUIRED,
            message="Authentication required.",
        )
    return session


def require_permission(permission: PermissionCode) -> Callable[[StoredSession, BootstrapAuthService], StoredSession]:
    """Build a dependency that requires a specific RBAC permission."""

    def dependency(
        session: StoredSession = Depends(require_authenticated_session),
        auth_service: BootstrapAuthService = Depends(get_auth_service),
    ) -> StoredSession:
        if not auth_service.has_permission(session, permission):
            raise ApiException(
                status_code=status.HTTP_403_FORBIDDEN,
                code=ApiErrorCode.PERMISSION_DENIED,
                message=f"Missing permission: {permission.value}",
                details={"required_permission": permission.value},
            )
        return session

    return dependency
