from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime

from robot_control_backend.bootstrap.settings import Settings
from robot_control_backend.domain.enums import AuditEventType, AuditOutcome, ModuleName, TaskStatus
from robot_control_backend.domain.models import AuditRecord, TaskRecord
from robot_control_backend.domain.state_machine import assert_transition_allowed
from robot_control_backend.task_service.models import (
    TaskAggregate,
    TaskCreateCommand,
    TaskPrerequisiteViolation,
    TaskStatusHistoryEntry,
)


class TaskServiceError(RuntimeError):
    """Base exception for task service failures."""


class TaskPrerequisiteError(TaskServiceError):
    """Raised when a task request is structurally valid but not executable yet."""

    def __init__(self, violations: list[TaskPrerequisiteViolation]) -> None:
        super().__init__("Task creation prerequisites were not met.")
        self.violations = violations


class TaskNotFoundError(TaskServiceError):
    """Raised when a task identifier cannot be resolved."""

    def __init__(self, task_id: str) -> None:
        super().__init__(f"Task '{task_id}' was not found.")
        self.task_id = task_id


class InMemoryTaskService:
    """Thread-safe in-process task service used until persistence arrives."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = threading.RLock()
        self._tasks: dict[str, TaskAggregate] = {}

    def create_task(self, command: TaskCreateCommand) -> TaskAggregate:
        """Create a task aggregate after business prerequisite checks pass."""
        violations = self._validate_create_prerequisites(command)
        if violations:
            raise TaskPrerequisiteError(violations)

        assert_transition_allowed(None, TaskStatus.CREATED)

        now = self._now()
        task_id = self._generate_id("task")
        task = TaskRecord(
            task_id=task_id,
            task_type=command.task_type,
            raw_instruction=command.raw_instruction,
            target_object=command.target_object,
            target_location=command.target_location,
            status=TaskStatus.CREATED,
            failure_reason=None,
            created_by=command.created_by,
            created_at=now,
            robot_id=self._settings.execution_robot_config_id or "",
            workstation_id=command.workstation_id,
        )

        aggregate = TaskAggregate(task=task)
        self._append_status_transition(
            aggregate,
            from_status=None,
            to_status=TaskStatus.CREATED,
            actor_id=command.created_by,
            reason="Task created and accepted by the API.",
            occurred_at=now,
        )
        aggregate.audit_records.insert(
            0,
            AuditRecord(
                audit_event_id=self._generate_id("audit"),
                task_id=task_id,
                event_type=AuditEventType.TASK_CREATED,
                source_module=ModuleName.TASK_SERVICE,
                outcome=AuditOutcome.SUCCESS,
                occurred_at=now,
                summary="Task created from API request.",
                actor_id=command.created_by,
                status_from=None,
                status_to=TaskStatus.CREATED,
                payload={
                    "task_type": command.task_type.value,
                    "raw_instruction": command.raw_instruction,
                    "target_object": command.target_object,
                    "target_location": command.target_location.model_dump(mode="json"),
                    "workstation_id": command.workstation_id,
                    "robot_id": task.robot_id,
                },
            ),
        )

        with self._lock:
            self._tasks[task_id] = aggregate
            return self._copy_aggregate(aggregate)

    def list_tasks(self, *, page: int, page_size: int) -> tuple[list[TaskRecord], int]:
        """Return paginated task summaries ordered by newest first."""
        with self._lock:
            ordered_tasks = sorted(
                (aggregate.task for aggregate in self._tasks.values()),
                key=lambda item: (item.created_at, item.task_id),
                reverse=True,
            )
            total = len(ordered_tasks)
            start = (page - 1) * page_size
            end = start + page_size
            page_items = ordered_tasks[start:end]
            return [task.model_copy(deep=True) for task in page_items], total

    def get_task(self, task_id: str) -> TaskRecord:
        """Return a single task summary or raise a not-found error."""
        return self.get_task_aggregate(task_id).task

    def get_task_aggregate(self, task_id: str) -> TaskAggregate:
        """Return the complete task aggregate for execution-chain queries."""
        with self._lock:
            aggregate = self._tasks.get(task_id)
            if aggregate is None:
                raise TaskNotFoundError(task_id)
            return self._copy_aggregate(aggregate)

    def _append_status_transition(
        self,
        aggregate: TaskAggregate,
        *,
        from_status: TaskStatus | None,
        to_status: TaskStatus,
        actor_id: str,
        reason: str,
        occurred_at: datetime,
    ) -> None:
        aggregate.status_history.append(
            TaskStatusHistoryEntry(
                history_id=self._generate_id("task-history"),
                task_id=aggregate.task.task_id,
                from_status=from_status,
                to_status=to_status,
                changed_at=occurred_at,
                changed_by=actor_id,
                reason=reason,
            )
        )
        aggregate.audit_records.append(
            AuditRecord(
                audit_event_id=self._generate_id("audit"),
                task_id=aggregate.task.task_id,
                event_type=AuditEventType.TASK_STATUS_CHANGED,
                source_module=ModuleName.TASK_SERVICE,
                outcome=AuditOutcome.SUCCESS,
                occurred_at=occurred_at,
                summary=f"Task status changed to {to_status.value}.",
                actor_id=actor_id,
                status_from=from_status,
                status_to=to_status,
                payload={"reason": reason},
            )
        )

    def _validate_create_prerequisites(self, command: TaskCreateCommand) -> list[TaskPrerequisiteViolation]:
        violations: list[TaskPrerequisiteViolation] = []

        if command.target_location.station_id != command.workstation_id:
            violations.append(
                TaskPrerequisiteViolation(
                    code="task.workstation_context_mismatch",
                    message="The task workstation_id must match target_location.station_id in the current single-workstation MVP.",
                )
            )

        if not self._settings.execution_robot_config_id:
            violations.append(
                TaskPrerequisiteViolation(
                    code="task.active_robot_config_missing",
                    message="RCA_EXECUTION_ROBOT_CONFIG_ID must be configured before tasks can enter the execution pipeline.",
                )
            )

        if not self._settings.safety_rule_set_id:
            violations.append(
                TaskPrerequisiteViolation(
                    code="task.safety_rule_set_missing",
                    message="RCA_SAFETY_RULE_SET_ID must be configured before tasks can enter the execution pipeline.",
                )
            )

        if not self._settings.safety_emergency_stop_enabled:
            violations.append(
                TaskPrerequisiteViolation(
                    code="task.emergency_stop_disabled",
                    message="RCA_SAFETY_EMERGENCY_STOP_ENABLED must remain true before tasks can enter the execution pipeline.",
                )
            )

        return violations

    @staticmethod
    def _copy_aggregate(aggregate: TaskAggregate) -> TaskAggregate:
        return aggregate.model_copy(deep=True)

    @staticmethod
    def _generate_id(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4()}"

    @staticmethod
    def _now() -> datetime:
        return datetime.now(tz=UTC)
