from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from robot_control_backend.domain.enums import (
    AlertEventType,
    AlertSeverity,
    AuditEventType,
    AuditOutcome,
)


class AuditTrailStage(str, Enum):
    """Top-level audit trail stages required by the Step 07 implementation plan."""

    INSTRUCTION = "instruction"
    CONTEXT_ASSEMBLY = "context_assembly"
    TOOL_CALL = "tool_call"
    AGENT_OUTPUT = "agent_output"
    VALIDATION = "validation"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    MEMORY_WRITE = "memory_write"
    ALERT = "alert"


@dataclass(frozen=True)
class AuditEventRule:
    """Declarative audit write rule used by future persistence services."""

    stage: AuditTrailStage
    description: str
    must_write: bool = True


@dataclass(frozen=True)
class AlertWriteRule:
    """Default alert severity and stop behavior for each alert event type."""

    severity: AlertSeverity
    emergency_stop_triggered: bool
    description: str


@dataclass(frozen=True)
class AlertEscalationRule:
    """Condition that turns an audit event into an alert event."""

    source_event_type: AuditEventType
    source_outcomes: frozenset[AuditOutcome]
    alert_event_type: AlertEventType
    description: str


AUDIT_EVENT_RULES: dict[AuditEventType, AuditEventRule] = {
    AuditEventType.TASK_CREATED: AuditEventRule(
        stage=AuditTrailStage.INSTRUCTION,
        description="Persist the original instruction submission and normalized task identity.",
    ),
    AuditEventType.CONTEXT_ASSEMBLED: AuditEventRule(
        stage=AuditTrailStage.CONTEXT_ASSEMBLY,
        description="Record the assembled runtime context sources before agent execution.",
    ),
    AuditEventType.TASK_STATUS_CHANGED: AuditEventRule(
        stage=AuditTrailStage.VALIDATION,
        description="Persist every task lifecycle transition for replay and debugging.",
    ),
    AuditEventType.KNOWLEDGE_RETRIEVED: AuditEventRule(
        stage=AuditTrailStage.CONTEXT_ASSEMBLY,
        description="Record retrieved knowledge, teaching samples, and their source identifiers.",
    ),
    AuditEventType.TOOL_CALLED: AuditEventRule(
        stage=AuditTrailStage.TOOL_CALL,
        description="Record a structured tool request summary and the returned facts.",
    ),
    AuditEventType.VISION_LOCATED: AuditEventRule(
        stage=AuditTrailStage.TOOL_CALL,
        description="Record pre-execution vision observations, detections, and risk findings.",
    ),
    AuditEventType.AGENT_OUTPUT_RECORDED: AuditEventRule(
        stage=AuditTrailStage.AGENT_OUTPUT,
        description="Record a structured agent output summary without raw reasoning traces.",
    ),
    AuditEventType.PLAN_GENERATED: AuditEventRule(
        stage=AuditTrailStage.AGENT_OUTPUT,
        description="Record the semantic action plan emitted by Planner.",
    ),
    AuditEventType.SCRIPT_GENERATED: AuditEventRule(
        stage=AuditTrailStage.AGENT_OUTPUT,
        description="Record the controlled script binding emitted by Coder.",
    ),
    AuditEventType.VALIDATION_COMPLETED: AuditEventRule(
        stage=AuditTrailStage.VALIDATION,
        description="Record Critic findings, run permission, and fallback direction.",
    ),
    AuditEventType.ROBOT_EXECUTED: AuditEventRule(
        stage=AuditTrailStage.EXECUTION,
        description="Record structured robot execution status and low-level error codes.",
    ),
    AuditEventType.VISION_VERIFIED: AuditEventRule(
        stage=AuditTrailStage.VERIFICATION,
        description="Record post-execution vision verification facts and acceptance result.",
    ),
    AuditEventType.MEMORY_WRITTEN: AuditEventRule(
        stage=AuditTrailStage.MEMORY_WRITE,
        description="Record successful long-term memory writes after verification passes.",
    ),
    AuditEventType.ALERT_CREATED: AuditEventRule(
        stage=AuditTrailStage.ALERT,
        description="Record alert creation details and its relationship to the triggering event.",
    ),
}


ALERT_WRITE_RULES: dict[AlertEventType, AlertWriteRule] = {
    AlertEventType.DANGEROUS_OBJECT_DETECTED: AlertWriteRule(
        severity=AlertSeverity.CRITICAL,
        emergency_stop_triggered=True,
        description="Dangerous objects in the workspace must force an immediate stop.",
    ),
    AlertEventType.VALIDATION_FAILED: AlertWriteRule(
        severity=AlertSeverity.HIGH,
        emergency_stop_triggered=False,
        description="Validation failures block execution but do not trigger a robot stop by default.",
    ),
    AlertEventType.EXECUTION_FAILED: AlertWriteRule(
        severity=AlertSeverity.CRITICAL,
        emergency_stop_triggered=True,
        description="Execution failures must stop the robot path and raise a high-priority alert.",
    ),
    AlertEventType.VERIFICATION_FAILED: AlertWriteRule(
        severity=AlertSeverity.HIGH,
        emergency_stop_triggered=True,
        description="Failed visual verification must stop further automatic actions until reviewed.",
    ),
    AlertEventType.EMERGENCY_STOPPED: AlertWriteRule(
        severity=AlertSeverity.CRITICAL,
        emergency_stop_triggered=True,
        description="Explicit emergency-stop events are always critical.",
    ),
}


ALERT_ESCALATION_RULES: tuple[AlertEscalationRule, ...] = (
    AlertEscalationRule(
        source_event_type=AuditEventType.VISION_LOCATED,
        source_outcomes=frozenset({AuditOutcome.EMERGENCY}),
        alert_event_type=AlertEventType.DANGEROUS_OBJECT_DETECTED,
        description="Dangerous detections from Vision must create a critical stop alert.",
    ),
    AlertEscalationRule(
        source_event_type=AuditEventType.VALIDATION_COMPLETED,
        source_outcomes=frozenset({AuditOutcome.FAILED}),
        alert_event_type=AlertEventType.VALIDATION_FAILED,
        description="Rejected validation decisions must create an execution-blocking alert.",
    ),
    AlertEscalationRule(
        source_event_type=AuditEventType.ROBOT_EXECUTED,
        source_outcomes=frozenset({AuditOutcome.FAILED, AuditOutcome.EMERGENCY}),
        alert_event_type=AlertEventType.EXECUTION_FAILED,
        description="Robot execution failures and emergency returns must raise an execution alert.",
    ),
    AlertEscalationRule(
        source_event_type=AuditEventType.VISION_VERIFIED,
        source_outcomes=frozenset({AuditOutcome.FAILED}),
        alert_event_type=AlertEventType.VERIFICATION_FAILED,
        description="Failed post-run verification must raise a verification alert.",
    ),
    AlertEscalationRule(
        source_event_type=AuditEventType.TASK_STATUS_CHANGED,
        source_outcomes=frozenset({AuditOutcome.EMERGENCY}),
        alert_event_type=AlertEventType.EMERGENCY_STOPPED,
        description="Emergency lifecycle transitions must emit an emergency-stop alert.",
    ),
)


FORBIDDEN_AUDIT_PAYLOAD_KEYS = frozenset(
    {
        "chain_of_thought",
        "raw_chain_of_thought",
        "thought",
        "thoughts",
        "internal_reasoning",
        "reasoning",
        "reasoning_trace",
        "scratchpad",
    }
)


def _normalize_key(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def find_forbidden_audit_payload_paths(payload: Any, *, _path: str = "payload") -> tuple[str, ...]:
    """Return the payload paths that contain forbidden raw reasoning keys."""

    forbidden_paths: list[str] = []

    if isinstance(payload, Mapping):
        for key, value in payload.items():
            child_path = f"{_path}.{key}"
            if _normalize_key(key) in FORBIDDEN_AUDIT_PAYLOAD_KEYS:
                forbidden_paths.append(child_path)
            forbidden_paths.extend(find_forbidden_audit_payload_paths(value, _path=child_path))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            forbidden_paths.extend(find_forbidden_audit_payload_paths(item, _path=f"{_path}[{index}]"))

    return tuple(forbidden_paths)


def assert_audit_payload_is_safe(payload: Any) -> None:
    """Raise when a payload contains raw reasoning keys forbidden by the MVP design."""

    forbidden_paths = find_forbidden_audit_payload_paths(payload)
    if forbidden_paths:
        joined_paths = ", ".join(forbidden_paths)
        raise ValueError(f"Audit payload contains forbidden raw reasoning fields: {joined_paths}")
