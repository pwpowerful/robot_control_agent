from __future__ import annotations

import math

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import Field, field_validator, model_validator

from robot_control_backend.api_server.contracts import (
    ApiErrorCode,
    ApiPayloadModel,
    ApiSuccessResponse,
    PaginationMeta,
    build_success_response,
    error_responses,
)
from robot_control_backend.api_server.deps import get_task_service, require_permission
from robot_control_backend.api_server.errors import ApiException
from robot_control_backend.api_server.routers._helpers import build_access_check_response
from robot_control_backend.auth.models import AccessCheckResponse
from robot_control_backend.auth.rbac import PermissionCode
from robot_control_backend.auth.service import StoredSession
from robot_control_backend.domain.models import AuditRecord, ExecutionPlan, ExecutionResult, SemanticActionPlan, TargetLocation, TaskRecord
from robot_control_backend.task_service import TaskCreateCommand, TaskNotFoundError, TaskPrerequisiteError, TaskStatusHistoryEntry
from robot_control_backend.task_service.service import InMemoryTaskService

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskApiModel(ApiPayloadModel):
    """Base API model for task endpoints."""


class TaskCreateRequest(TaskApiModel):
    """Task creation payload accepted by the Step 11 API."""

    raw_instruction: str = Field(description="Original natural-language instruction.")
    target_object: str = Field(description="Target object type to pick.")
    workstation_id: str = Field(description="Single-workstation context identifier.")
    target_location: TargetLocation = Field(description="Requested target placement location.")

    @field_validator("raw_instruction", "target_object", "workstation_id")
    @classmethod
    def _normalize_required_strings(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @model_validator(mode="after")
    def _validate_nested_location_fields(self) -> TaskCreateRequest:
        station_id = self.target_location.station_id.strip()
        if not station_id:
            raise ValueError("target_location.station_id must not be empty")

        frame_id = self.target_location.pose.frame_id.strip()
        if not frame_id:
            raise ValueError("target_location.pose.frame_id must not be empty")

        if self.target_location.tolerance_mm <= 0:
            raise ValueError("target_location.tolerance_mm must be greater than 0")

        slot_id = self.target_location.slot_id.strip() if self.target_location.slot_id else None
        self.target_location = self.target_location.model_copy(
            update={
                "station_id": station_id,
                "slot_id": slot_id or None,
                "pose": self.target_location.pose.model_copy(update={"frame_id": frame_id}),
            }
        )
        return self


class TaskListResponse(TaskApiModel):
    """Paginated task list payload returned by the Step 11 API."""

    items: list[TaskRecord] = Field(description="Task summaries for the requested page.")


class TaskExecutionChainResponse(TaskApiModel):
    """Task execution-chain payload returned by the Step 11 API."""

    task: TaskRecord = Field(description="Current task summary.")
    status_history: list[TaskStatusHistoryEntry] = Field(
        default_factory=list,
        description="Chronological task status history.",
    )
    audit_chain: list[AuditRecord] = Field(
        default_factory=list,
        description="Chronological audit chain for the task.",
    )
    semantic_action_plan: SemanticActionPlan | None = Field(
        default=None,
        description="Planner output when available.",
    )
    execution_plan: ExecutionPlan | None = Field(
        default=None,
        description="Coder execution plan when available.",
    )
    execution_result: ExecutionResult | None = Field(
        default=None,
        description="Execution result when available.",
    )


@router.get(
    "/_access-check",
    response_model=ApiSuccessResponse[AccessCheckResponse],
    responses=error_responses(401, 403, 500),
)
def check_task_access(
    request: Request,
    _: object = Depends(require_permission(PermissionCode.TASK_READ)),
) -> ApiSuccessResponse[AccessCheckResponse]:
    """Verify access to the task list and detail interface group."""
    return build_access_check_response(
        request,
        scope="tasks",
        permission=PermissionCode.TASK_READ,
        message="Task access granted.",
    )


@router.post(
    "",
    response_model=ApiSuccessResponse[TaskRecord],
    responses=error_responses(401, 403, 422, 500),
)
def create_task(
    payload: TaskCreateRequest,
    request: Request,
    session: StoredSession = Depends(require_permission(PermissionCode.TASK_CREATE)),
    task_service: InMemoryTaskService = Depends(get_task_service),
) -> ApiSuccessResponse[TaskRecord]:
    """Create a new task after minimum execution prerequisites are validated."""
    try:
        aggregate = task_service.create_task(
            TaskCreateCommand(
                raw_instruction=payload.raw_instruction,
                target_object=payload.target_object,
                target_location=payload.target_location,
                workstation_id=payload.workstation_id,
                created_by=session.user.username,
            )
        )
    except TaskPrerequisiteError as exc:
        raise ApiException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code=ApiErrorCode.TASK_PREREQUISITE_FAILED,
            message="Task creation prerequisites were not met.",
            details=[violation.model_dump(mode="json") for violation in exc.violations],
        ) from exc

    return build_success_response(request, aggregate.task)


@router.get(
    "",
    response_model=ApiSuccessResponse[TaskListResponse],
    responses=error_responses(401, 403, 422, 500),
)
def list_tasks(
    request: Request,
    page: int = Query(default=1, ge=1, description="1-based page number."),
    page_size: int = Query(default=20, ge=1, le=100, description="Maximum tasks returned in one page."),
    _: StoredSession = Depends(require_permission(PermissionCode.TASK_READ)),
    task_service: InMemoryTaskService = Depends(get_task_service),
) -> ApiSuccessResponse[TaskListResponse]:
    """Return task summaries ordered by newest creation time first."""
    items, total = task_service.list_tasks(page=page, page_size=page_size)
    total_pages = math.ceil(total / page_size) if total else 0
    return build_success_response(
        request,
        TaskListResponse(items=items),
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.get(
    "/{task_id}",
    response_model=ApiSuccessResponse[TaskRecord],
    responses=error_responses(401, 403, 404, 500),
)
def get_task_detail(
    task_id: str,
    request: Request,
    _: StoredSession = Depends(require_permission(PermissionCode.TASK_DETAIL_READ)),
    task_service: InMemoryTaskService = Depends(get_task_service),
) -> ApiSuccessResponse[TaskRecord]:
    """Return the current task detail summary required by the console."""
    try:
        task = task_service.get_task(task_id)
    except TaskNotFoundError as exc:
        raise ApiException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ApiErrorCode.TASK_NOT_FOUND,
            message=str(exc),
            details={"task_id": task_id},
        ) from exc

    return build_success_response(request, task)


@router.get(
    "/{task_id}/execution-chain",
    response_model=ApiSuccessResponse[TaskExecutionChainResponse],
    responses=error_responses(401, 403, 404, 500),
)
def get_task_execution_chain(
    task_id: str,
    request: Request,
    _: StoredSession = Depends(require_permission(PermissionCode.EXECUTION_VIEW)),
    task_service: InMemoryTaskService = Depends(get_task_service),
) -> ApiSuccessResponse[TaskExecutionChainResponse]:
    """Return the current execution-chain view including status history and audit chain."""
    try:
        aggregate = task_service.get_task_aggregate(task_id)
    except TaskNotFoundError as exc:
        raise ApiException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ApiErrorCode.TASK_NOT_FOUND,
            message=str(exc),
            details={"task_id": task_id},
        ) from exc

    return build_success_response(
        request,
        TaskExecutionChainResponse(
            task=aggregate.task,
            status_history=aggregate.status_history,
            audit_chain=aggregate.audit_records,
            semantic_action_plan=aggregate.semantic_action_plan,
            execution_plan=aggregate.execution_plan,
            execution_result=aggregate.execution_result,
        ),
    )
