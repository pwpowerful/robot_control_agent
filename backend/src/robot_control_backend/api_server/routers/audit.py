from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from robot_control_backend.api_server.contracts import ApiSuccessResponse, error_responses
from robot_control_backend.api_server.deps import require_permission
from robot_control_backend.api_server.routers._helpers import build_access_check_response
from robot_control_backend.auth.models import AccessCheckResponse
from robot_control_backend.auth.rbac import PermissionCode

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get(
    "/_access-check",
    response_model=ApiSuccessResponse[AccessCheckResponse],
    responses=error_responses(401, 403, 500),
)
def check_audit_access(
    request: Request,
    _: object = Depends(require_permission(PermissionCode.AUDIT_READ)),
) -> ApiSuccessResponse[AccessCheckResponse]:
    """Verify access to audit queries."""
    return build_access_check_response(
        request,
        scope="audit",
        permission=PermissionCode.AUDIT_READ,
        message="Audit access granted.",
    )
