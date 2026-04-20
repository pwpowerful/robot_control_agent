from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from robot_control_backend.api_server.contracts import ApiSuccessResponse, error_responses
from robot_control_backend.api_server.deps import require_permission
from robot_control_backend.api_server.routers._helpers import build_access_check_response
from robot_control_backend.auth.models import AccessCheckResponse
from robot_control_backend.auth.rbac import PermissionCode

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get(
    "/_access-check",
    response_model=ApiSuccessResponse[AccessCheckResponse],
    responses=error_responses(401, 403, 500),
)
def check_alert_access(
    request: Request,
    _: object = Depends(require_permission(PermissionCode.ALERT_READ)),
) -> ApiSuccessResponse[AccessCheckResponse]:
    """Verify access to alert viewing capabilities."""
    return build_access_check_response(
        request,
        scope="alerts",
        permission=PermissionCode.ALERT_READ,
        message="Alert view access granted.",
    )


@router.post(
    "/_handle-check",
    response_model=ApiSuccessResponse[AccessCheckResponse],
    responses=error_responses(401, 403, 500),
)
def check_alert_handle_access(
    request: Request,
    _: object = Depends(require_permission(PermissionCode.ALERT_HANDLE)),
) -> ApiSuccessResponse[AccessCheckResponse]:
    """Verify access to admin-only alert handling capabilities."""
    return build_access_check_response(
        request,
        scope="alerts.handle",
        permission=PermissionCode.ALERT_HANDLE,
        message="Alert handling access granted.",
    )
