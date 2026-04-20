from __future__ import annotations

from fastapi import Request

from robot_control_backend.api_server.contracts import ApiSuccessResponse, build_success_response
from robot_control_backend.auth.models import AccessCheckResponse
from robot_control_backend.auth.rbac import PermissionCode


def build_access_check_response(
    request: Request,
    *,
    scope: str,
    permission: PermissionCode,
    message: str,
) -> ApiSuccessResponse[AccessCheckResponse]:
    """Build a structured access-check response inside the shared success envelope."""
    return build_success_response(
        request,
        AccessCheckResponse(
            scope=scope,
            required_permission=permission.value,
            allowed=True,
            message=message,
        ),
    )
