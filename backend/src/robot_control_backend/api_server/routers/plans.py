from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from robot_control_backend.api_server.contracts import ApiSuccessResponse, error_responses
from robot_control_backend.api_server.deps import require_permission
from robot_control_backend.api_server.routers._helpers import build_access_check_response
from robot_control_backend.auth.models import AccessCheckResponse
from robot_control_backend.auth.rbac import PermissionCode

router = APIRouter(prefix="/api/plans", tags=["plans"])


@router.get(
    "/_access-check",
    response_model=ApiSuccessResponse[AccessCheckResponse],
    responses=error_responses(401, 403, 500),
)
def check_plan_and_script_access(
    request: Request,
    _: object = Depends(require_permission(PermissionCode.EXECUTION_VIEW)),
) -> ApiSuccessResponse[AccessCheckResponse]:
    """Verify access to plan and script summaries tied to task execution."""
    return build_access_check_response(
        request,
        scope="plans",
        permission=PermissionCode.EXECUTION_VIEW,
        message="Plan and script access granted.",
    )
