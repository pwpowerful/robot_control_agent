from __future__ import annotations

import pytest

from robot_control_backend.domain.enums import TaskStatus
from robot_control_backend.domain.state_machine import (
    TASK_STATE_RULES,
    StateTransitionError,
    assert_transition_allowed,
)


def test_state_machine_covers_happy_path() -> None:
    happy_path = [
        None,
        TaskStatus.CREATED,
        TaskStatus.PLANNING,
        TaskStatus.VALIDATING,
        TaskStatus.READY_TO_RUN,
        TaskStatus.RUNNING,
        TaskStatus.VERIFYING,
        TaskStatus.SUCCEEDED,
    ]

    for previous, current in zip(happy_path, happy_path[1:]):
        assert_transition_allowed(previous, current)


def test_state_machine_covers_retry_and_failure_flows() -> None:
    assert_transition_allowed(TaskStatus.VALIDATING, TaskStatus.PLANNING)
    assert_transition_allowed(TaskStatus.PLANNING, TaskStatus.FAILED)
    assert_transition_allowed(TaskStatus.RUNNING, TaskStatus.FAILED)
    assert_transition_allowed(TaskStatus.RUNNING, TaskStatus.EMERGENCY_STOPPED)
    assert_transition_allowed(TaskStatus.VERIFYING, TaskStatus.FAILED)


def test_state_machine_rejects_ambiguous_or_illegal_transitions() -> None:
    with pytest.raises(StateTransitionError):
        assert_transition_allowed(TaskStatus.CREATED, TaskStatus.READY_TO_RUN)

    with pytest.raises(StateTransitionError):
        assert_transition_allowed(TaskStatus.SUCCEEDED, TaskStatus.RUNNING)

    assert set(TASK_STATE_RULES.keys()) == set(TaskStatus)
