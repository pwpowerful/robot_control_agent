from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from robot_control_backend.api_server.contracts import ApiSuccessResponse, error_responses
from robot_control_backend.api_server.deps import require_permission
from robot_control_backend.api_server.routers._helpers import build_access_check_response
from robot_control_backend.auth.models import AccessCheckResponse
from robot_control_backend.auth.rbac import PermissionCode

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post(
    "/items/_access-check",
    response_model=ApiSuccessResponse[AccessCheckResponse],
    responses=error_responses(401, 403, 500),
)
def check_knowledge_items_access(
    request: Request,
    _: object = Depends(require_permission(PermissionCode.KNOWLEDGE_ITEMS_MANAGE)),
) -> ApiSuccessResponse[AccessCheckResponse]:
    """Verify access to knowledge item management."""
    return build_access_check_response(
        request,
        scope="knowledge.items",
        permission=PermissionCode.KNOWLEDGE_ITEMS_MANAGE,
        message="Knowledge item access granted.",
    )


@router.post(
    "/samples/_access-check",
    response_model=ApiSuccessResponse[AccessCheckResponse],
    responses=error_responses(401, 403, 500),
)
def check_teaching_samples_access(
    request: Request,
    _: object = Depends(require_permission(PermissionCode.TEACHING_SAMPLES_MANAGE)),
) -> ApiSuccessResponse[AccessCheckResponse]:
    """Verify access to teaching sample management."""
    return build_access_check_response(
        request,
        scope="knowledge.samples",
        permission=PermissionCode.TEACHING_SAMPLES_MANAGE,
        message="Teaching sample access granted.",
    )
