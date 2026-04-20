from __future__ import annotations

from datetime import datetime

from pydantic import Field

from robot_control_backend.domain.models import (
    AuditRecord,
    DomainModel,
    ExecutionPlan,
    ExecutionResult,
    SemanticActionPlan,
    TargetLocation,
    TaskRecord,
)
from robot_control_backend.domain.enums import TaskStatus, TaskType


class TaskCreateCommand(DomainModel):
    """Normalized task creation command consumed by the task service."""

    raw_instruction: str = Field(description="Original natural-language instruction submitted by the caller.")
    target_object: str = Field(description="Normalized target object requested by the caller.")
    target_location: TargetLocation = Field(description="Requested placement location.")
    workstation_id: str = Field(description="Single-workstation context for the task.")
    created_by: str = Field(description="Username or user identifier that submitted the task.")
    task_type: TaskType = Field(default=TaskType.PICK_AND_PLACE, description="Normalized task type.")


class TaskPrerequisiteViolation(DomainModel):
    """Single business prerequisite violation that blocks task creation."""

    code: str = Field(description="Stable prerequisite violation code.")
    message: str = Field(description="Human-readable explanation safe to surface in the UI.")


class TaskStatusHistoryEntry(DomainModel):
    """Recorded task status transition kept alongside the task aggregate."""

    history_id: str = Field(description="Status history entry identifier.")
    task_id: str = Field(description="Associated task identifier.")
    from_status: TaskStatus | None = Field(default=None, description="Previous task status, if any.")
    to_status: TaskStatus = Field(description="New task status recorded by this entry.")
    changed_at: datetime = Field(description="Timestamp when the transition was recorded.")
    changed_by: str = Field(description="Actor that caused the transition.")
    reason: str = Field(description="Human-readable explanation for the transition.")


class TaskAggregate(DomainModel):
    """In-memory task aggregate used by the Step 11 API layer."""

    task: TaskRecord = Field(description="Current task state.")
    status_history: list[TaskStatusHistoryEntry] = Field(
        default_factory=list,
        description="Chronological task status history entries.",
    )
    audit_records: list[AuditRecord] = Field(
        default_factory=list,
        description="Chronological audit records attached to the task.",
    )
    semantic_action_plan: SemanticActionPlan | None = Field(
        default=None,
        description="Planner output when available.",
    )
    execution_plan: ExecutionPlan | None = Field(
        default=None,
        description="Coder output when available.",
    )
    execution_result: ExecutionResult | None = Field(
        default=None,
        description="Robot execution result when available.",
    )
