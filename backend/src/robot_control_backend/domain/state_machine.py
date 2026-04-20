from __future__ import annotations

from dataclasses import dataclass

from robot_control_backend.domain.enums import TaskStatus


@dataclass(frozen=True)
class FailureTransitionRule:
    """Failure trigger and its target status."""

    trigger: str
    target_status: TaskStatus


@dataclass(frozen=True)
class TaskStateRule:
    """Rule set describing one task lifecycle state."""

    status: TaskStatus
    purpose: str
    allowed_previous_statuses: tuple[TaskStatus, ...]
    allowed_next_statuses: tuple[TaskStatus, ...]
    entry_conditions: tuple[str, ...]
    exit_conditions: tuple[str, ...]
    failure_transitions: tuple[FailureTransitionRule, ...]
    is_terminal: bool = False


class StateTransitionError(ValueError):
    """Raised when an illegal task status transition is requested."""


TASK_STATE_RULES: dict[TaskStatus, TaskStateRule] = {
    TaskStatus.CREATED: TaskStateRule(
        status=TaskStatus.CREATED,
        purpose="Task record exists and is waiting to enter the execution pipeline.",
        allowed_previous_statuses=(),
        allowed_next_statuses=(TaskStatus.PLANNING,),
        entry_conditions=(
            "Task ID, raw instruction, target object, target location, creator, robot ID, and workstation ID are present.",
            "Task has been accepted by the API layer as a valid MVP task shape.",
        ),
        exit_conditions=(
            "Execution worker has claimed the task and loaded active robot and safety context.",
        ),
        failure_transitions=(
            FailureTransitionRule(
                trigger="Task creation is rejected before persistence.",
                target_status=TaskStatus.FAILED,
            ),
        ),
    ),
    TaskStatus.PLANNING: TaskStateRule(
        status=TaskStatus.PLANNING,
        purpose="Planner is producing a semantic action plan and Coder is materializing the execution-level artifacts required before Critic validation.",
        allowed_previous_statuses=(TaskStatus.CREATED, TaskStatus.VALIDATING),
        allowed_next_statuses=(TaskStatus.VALIDATING, TaskStatus.FAILED, TaskStatus.EMERGENCY_STOPPED),
        entry_conditions=(
            "Task is in created state or is retrying after a validation-directed return to Planner.",
            "Vision locate result and knowledge retrieval context are available for the task.",
            "Active safety rule snapshot is available.",
        ),
        exit_conditions=(
            "Planner produced a semantic action plan and Coder produced the execution plan plus controlled script summary.",
            "Planning concluded with a terminal user-readable failure.",
        ),
        failure_transitions=(
            FailureTransitionRule(
                trigger="Target object cannot be located, required fields are incomplete, or retry budget is exhausted.",
                target_status=TaskStatus.FAILED,
            ),
            FailureTransitionRule(
                trigger="Dangerous object is detected in the workspace during planning prerequisites.",
                target_status=TaskStatus.EMERGENCY_STOPPED,
            ),
        ),
    ),
    TaskStatus.VALIDATING: TaskStateRule(
        status=TaskStatus.VALIDATING,
        purpose="Critic is validating the execution-level structured plan and controlled script before execution.",
        allowed_previous_statuses=(TaskStatus.PLANNING,),
        allowed_next_statuses=(
            TaskStatus.PLANNING,
            TaskStatus.READY_TO_RUN,
            TaskStatus.FAILED,
            TaskStatus.EMERGENCY_STOPPED,
        ),
        entry_conditions=(
            "Semantic action plan exists and has already been materialized into an execution plan.",
            "Execution plan exists and has been translated into a controlled script summary.",
            "All action templates and parameters are available for Critic checks.",
        ),
        exit_conditions=(
            "Validation passed and the task is cleared for execution.",
            "Validation failed and either returns to Planner for another attempt or becomes terminal.",
        ),
        failure_transitions=(
            FailureTransitionRule(
                trigger="Critic finds a fixable issue and remaining retry budget allows a return to Planner.",
                target_status=TaskStatus.PLANNING,
            ),
            FailureTransitionRule(
                trigger="Critic rejects the task with a terminal issue or the retry budget is exhausted.",
                target_status=TaskStatus.FAILED,
            ),
            FailureTransitionRule(
                trigger="A safety stop is raised while validation is in progress.",
                target_status=TaskStatus.EMERGENCY_STOPPED,
            ),
        ),
    ),
    TaskStatus.READY_TO_RUN: TaskStateRule(
        status=TaskStatus.READY_TO_RUN,
        purpose="Task passed validation and is queued for the single execution slot.",
        allowed_previous_statuses=(TaskStatus.VALIDATING,),
        allowed_next_statuses=(TaskStatus.RUNNING, TaskStatus.FAILED, TaskStatus.EMERGENCY_STOPPED),
        entry_conditions=(
            "Validation result is allowed_to_run = true.",
            "Task owns the single-workstation execution slot.",
        ),
        exit_conditions=(
            "Robot execution request has been dispatched to the robot adapter.",
        ),
        failure_transitions=(
            FailureTransitionRule(
                trigger="Execution prerequisites become invalid before dispatch, such as configuration loss or queue timeout.",
                target_status=TaskStatus.FAILED,
            ),
            FailureTransitionRule(
                trigger="Emergency stop is triggered before robot dispatch completes.",
                target_status=TaskStatus.EMERGENCY_STOPPED,
            ),
        ),
    ),
    TaskStatus.RUNNING: TaskStateRule(
        status=TaskStatus.RUNNING,
        purpose="Robot adapter is executing the approved controlled action sequence.",
        allowed_previous_statuses=(TaskStatus.READY_TO_RUN,),
        allowed_next_statuses=(TaskStatus.VERIFYING, TaskStatus.FAILED, TaskStatus.EMERGENCY_STOPPED),
        entry_conditions=(
            "Validated controlled script has been dispatched to the robot adapter.",
            "Robot adapter accepted the task and began execution.",
        ),
        exit_conditions=(
            "Robot adapter completed execution and returned a structured execution result.",
        ),
        failure_transitions=(
            FailureTransitionRule(
                trigger="Robot returns execution interrupted, grasp slip, object not found, workspace violation, or collision result.",
                target_status=TaskStatus.FAILED,
            ),
            FailureTransitionRule(
                trigger="Emergency stop is triggered during robot execution.",
                target_status=TaskStatus.EMERGENCY_STOPPED,
            ),
        ),
    ),
    TaskStatus.VERIFYING: TaskStateRule(
        status=TaskStatus.VERIFYING,
        purpose="Post-execution vision verification is deciding whether the task truly succeeded.",
        allowed_previous_statuses=(TaskStatus.RUNNING,),
        allowed_next_statuses=(TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.EMERGENCY_STOPPED),
        entry_conditions=(
            "Robot execution completed without terminal robot failure.",
            "Post-execution vision verification request has been issued.",
        ),
        exit_conditions=(
            "Vision verification concluded with either accepted placement or a terminal failure result.",
        ),
        failure_transitions=(
            FailureTransitionRule(
                trigger="Verification confidence is below threshold or placement deviation exceeds tolerance.",
                target_status=TaskStatus.FAILED,
            ),
            FailureTransitionRule(
                trigger="Emergency stop is triggered during post-execution verification.",
                target_status=TaskStatus.EMERGENCY_STOPPED,
            ),
        ),
    ),
    TaskStatus.SUCCEEDED: TaskStateRule(
        status=TaskStatus.SUCCEEDED,
        purpose="Task finished successfully and may write a long-term memory record.",
        allowed_previous_statuses=(TaskStatus.VERIFYING,),
        allowed_next_statuses=(),
        entry_conditions=(
            "Vision verification passed the configured confidence and placement tolerance checks.",
            "Task result is complete and may be persisted for history and memory writing.",
        ),
        exit_conditions=(),
        failure_transitions=(),
        is_terminal=True,
    ),
    TaskStatus.FAILED: TaskStateRule(
        status=TaskStatus.FAILED,
        purpose="Task ended in a terminal non-emergency failure state.",
        allowed_previous_statuses=(
            TaskStatus.PLANNING,
            TaskStatus.VALIDATING,
            TaskStatus.READY_TO_RUN,
            TaskStatus.RUNNING,
            TaskStatus.VERIFYING,
        ),
        allowed_next_statuses=(),
        entry_conditions=(
            "Task has a normalized failure category and a user-readable failure reason.",
            "Automatic retry has stopped for the current task instance.",
        ),
        exit_conditions=(),
        failure_transitions=(),
        is_terminal=True,
    ),
    TaskStatus.EMERGENCY_STOPPED: TaskStateRule(
        status=TaskStatus.EMERGENCY_STOPPED,
        purpose="Task entered the terminal emergency state because a safety stop was triggered.",
        allowed_previous_statuses=(
            TaskStatus.PLANNING,
            TaskStatus.VALIDATING,
            TaskStatus.READY_TO_RUN,
            TaskStatus.RUNNING,
            TaskStatus.VERIFYING,
        ),
        allowed_next_statuses=(),
        entry_conditions=(
            "A dangerous-object detection, emergency-stop command, or equivalent safety-stop event was raised.",
            "Robot adapter safety stop path has been invoked or confirmed.",
        ),
        exit_conditions=(),
        failure_transitions=(),
        is_terminal=True,
    ),
}


def get_state_rule(status: TaskStatus) -> TaskStateRule:
    """Return the rule definition for a task lifecycle status."""

    return TASK_STATE_RULES[status]


def is_terminal_status(status: TaskStatus) -> bool:
    """Return whether a task status is terminal."""

    return TASK_STATE_RULES[status].is_terminal


def assert_transition_allowed(
    from_status: TaskStatus | None,
    to_status: TaskStatus,
) -> None:
    """Validate a task status transition against the shared state machine."""

    if from_status is None:
        if to_status is not TaskStatus.CREATED:
            raise StateTransitionError("Only the created status may be entered from a null state.")
        return

    from_rule = TASK_STATE_RULES[from_status]
    to_rule = TASK_STATE_RULES[to_status]

    if to_status not in from_rule.allowed_next_statuses:
        raise StateTransitionError(
            f"Illegal task transition: {from_status.value} -> {to_status.value}"
        )

    if from_status not in to_rule.allowed_previous_statuses:
        raise StateTransitionError(
            f"Transition target {to_status.value} does not accept previous status {from_status.value}"
        )
