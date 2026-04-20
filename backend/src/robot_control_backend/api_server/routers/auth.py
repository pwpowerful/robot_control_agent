from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status

from robot_control_backend.api_server.contracts import ApiErrorCode, ApiSuccessResponse, build_success_response, error_responses
from robot_control_backend.api_server.deps import get_app_settings, get_auth_service, require_authenticated_session
from robot_control_backend.api_server.errors import ApiException
from robot_control_backend.auth.models import ActiveSessionResponse, LoginRequest, LogoutResponse, PermissionMatrixResponse
from robot_control_backend.auth.service import AuthenticationError, BootstrapAuthService, StoredSession
from robot_control_backend.bootstrap.settings import Settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=ApiSuccessResponse[ActiveSessionResponse],
    responses=error_responses(401, 422, 500),
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    settings: Settings = Depends(get_app_settings),
    auth_service: BootstrapAuthService = Depends(get_auth_service),
) -> ApiSuccessResponse[ActiveSessionResponse]:
    """Authenticate a bootstrap user and issue an HTTP-only session cookie."""
    try:
        raw_token, session = auth_service.login(
            username=payload.username,
            password=payload.password,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except AuthenticationError as exc:
        raise ApiException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.INVALID_CREDENTIALS,
            message="Invalid username or password.",
        ) from exc

    response.set_cookie(
        key=settings.auth.session_cookie_name,
        value=raw_token,
        max_age=settings.auth.session_ttl_minutes * 60,
        httponly=True,
        secure=settings.auth.require_secure_cookies,
        samesite=settings.auth.cookie_same_site,
        path="/",
    )
    return build_success_response(request, auth_service.build_session_response(session))


@router.post(
    "/logout",
    response_model=ApiSuccessResponse[LogoutResponse],
    responses=error_responses(500),
)
def logout(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_app_settings),
    auth_service: BootstrapAuthService = Depends(get_auth_service),
) -> ApiSuccessResponse[LogoutResponse]:
    """Revoke the current session and remove the cookie from the browser."""
    auth_service.revoke_session(request.cookies.get(settings.auth.session_cookie_name))
    response.delete_cookie(
        key=settings.auth.session_cookie_name,
        path="/",
        httponly=True,
        secure=settings.auth.require_secure_cookies,
        samesite=settings.auth.cookie_same_site,
    )
    return build_success_response(request, LogoutResponse(status="logged_out"))


@router.get(
    "/me",
    response_model=ApiSuccessResponse[ActiveSessionResponse],
    responses=error_responses(401, 500),
)
def get_current_session(
    request: Request,
    session: StoredSession = Depends(require_authenticated_session),
    auth_service: BootstrapAuthService = Depends(get_auth_service),
) -> ApiSuccessResponse[ActiveSessionResponse]:
    """Return the currently authenticated user and effective permissions."""
    return build_success_response(request, auth_service.build_session_response(session))


@router.get(
    "/permission-matrix",
    response_model=ApiSuccessResponse[PermissionMatrixResponse],
    responses=error_responses(401, 500),
)
def get_permission_matrix(
    request: Request,
    _: StoredSession = Depends(require_authenticated_session),
    auth_service: BootstrapAuthService = Depends(get_auth_service),
) -> ApiSuccessResponse[PermissionMatrixResponse]:
    """Return the canonical RBAC matrix for the current MVP."""
    return build_success_response(request, auth_service.permission_matrix())
