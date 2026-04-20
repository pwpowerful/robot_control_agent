from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from robot_control_backend import __version__
from robot_control_backend.api_server.contracts import API_VERSION, ApiPayloadModel, ApiSuccessResponse, build_success_response, error_responses
from robot_control_backend.api_server.deps import get_app_settings, get_auth_service
from robot_control_backend.auth.service import BootstrapAuthService
from robot_control_backend.bootstrap.settings import Settings

router = APIRouter(prefix="/api/system", tags=["system"])


class SystemCheckStatus(ApiPayloadModel):
    """Single system-health check item."""

    name: str
    status: str
    detail: str


class SystemHealthResponse(ApiPayloadModel):
    """Health-check payload for the current backend instance."""

    status: str
    app_name: str
    environment: str
    checks: list[SystemCheckStatus]


class SystemVersionResponse(ApiPayloadModel):
    """Version payload exposed by the backend API."""

    app_name: str
    app_version: str
    api_version: str
    environment: str
    docs_url: str | None
    redoc_url: str | None
    openapi_url: str | None
    session_backend: str


@router.get(
    "/health",
    response_model=ApiSuccessResponse[SystemHealthResponse],
    responses=error_responses(500),
)
def get_system_health(
    request: Request,
    settings: Settings = Depends(get_app_settings),
    auth_service: BootstrapAuthService = Depends(get_auth_service),
) -> ApiSuccessResponse[SystemHealthResponse]:
    """Return the minimal health status for the backend foundation."""
    return build_success_response(
        request,
        SystemHealthResponse(
            status="ok",
            app_name=settings.app_name,
            environment=settings.app_env.value,
            checks=[
                SystemCheckStatus(
                    name="settings",
                    status="ok",
                    detail=f"Configuration loaded for {settings.app_env.value}.",
                ),
                SystemCheckStatus(
                    name="auth_session_backend",
                    status="ok",
                    detail=auth_service.session_backend_name,
                ),
            ],
        ),
    )


@router.get(
    "/version",
    response_model=ApiSuccessResponse[SystemVersionResponse],
    responses=error_responses(500),
)
def get_system_version(
    request: Request,
    settings: Settings = Depends(get_app_settings),
    auth_service: BootstrapAuthService = Depends(get_auth_service),
) -> ApiSuccessResponse[SystemVersionResponse]:
    """Return package and API contract version metadata."""
    return build_success_response(
        request,
        SystemVersionResponse(
            app_name=settings.app_name,
            app_version=__version__,
            api_version=API_VERSION,
            environment=settings.app_env.value,
            docs_url=request.app.docs_url,
            redoc_url=request.app.redoc_url,
            openapi_url=request.app.openapi_url,
            session_backend=auth_service.session_backend_name,
        ),
    )
