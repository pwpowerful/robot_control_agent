from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from robot_control_backend.api_server.contracts import ApiSuccessResponse, error_responses
from robot_control_backend.api_server.deps import require_permission
from robot_control_backend.api_server.routers._helpers import build_access_check_response
from robot_control_backend.auth.models import AccessCheckResponse
from robot_control_backend.auth.rbac import PermissionCode

router = APIRouter(prefix="/api/config", tags=["config"])


@router.post(
    "/robot/_access-check",
    response_model=ApiSuccessResponse[AccessCheckResponse],
    responses=error_responses(401, 403, 500),
)
def check_robot_config_access(
    request: Request,
    _: object = Depends(require_permission(PermissionCode.ROBOT_CONFIG_MANAGE)),
) -> ApiSuccessResponse[AccessCheckResponse]:
    """Verify access to robot configuration management."""
    return build_access_check_response(
        request,
        scope="config.robot",
        permission=PermissionCode.ROBOT_CONFIG_MANAGE,
        message="Robot configuration access granted.",
    )


@router.post(
    "/safety-rules/_access-check",
    response_model=ApiSuccessResponse[AccessCheckResponse],
    responses=error_responses(401, 403, 500),
)
def check_safety_rules_access(
    request: Request,
    _: object = Depends(require_permission(PermissionCode.SAFETY_RULES_MANAGE)),
) -> ApiSuccessResponse[AccessCheckResponse]:
    """Verify access to safety rule set management."""
    return build_access_check_response(
        request,
        scope="config.safety_rules",
        permission=PermissionCode.SAFETY_RULES_MANAGE,
        message="Safety rule access granted.",
    )
