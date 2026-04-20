from __future__ import annotations

import pytest

from robot_control_backend.audit import (
    ALERT_ESCALATION_RULES,
    ALERT_WRITE_RULES,
    AUDIT_EVENT_RULES,
    AlertWriteRule,
    AuditTrailStage,
    assert_audit_payload_is_safe,
    find_forbidden_audit_payload_paths,
)
from robot_control_backend.domain.enums import (
    AlertEventType,
    AlertSeverity,
    AuditEventType,
    AuditOutcome,
)


def test_audit_event_rules_cover_step_07_end_to_end_stages() -> None:
    covered_stages = {rule.stage for rule in AUDIT_EVENT_RULES.values()}

    assert {
        AuditTrailStage.INSTRUCTION,
        AuditTrailStage.CONTEXT_ASSEMBLY,
        AuditTrailStage.TOOL_CALL,
        AuditTrailStage.AGENT_OUTPUT,
        AuditTrailStage.VALIDATION,
        AuditTrailStage.EXECUTION,
        AuditTrailStage.VERIFICATION,
        AuditTrailStage.MEMORY_WRITE,
        AuditTrailStage.ALERT,
    } <= covered_stages
    assert AUDIT_EVENT_RULES[AuditEventType.CONTEXT_ASSEMBLED].stage is AuditTrailStage.CONTEXT_ASSEMBLY
    assert AUDIT_EVENT_RULES[AuditEventType.TOOL_CALLED].stage is AuditTrailStage.TOOL_CALL
    assert AUDIT_EVENT_RULES[AuditEventType.AGENT_OUTPUT_RECORDED].stage is AuditTrailStage.AGENT_OUTPUT


def test_alert_write_rules_capture_default_severity_and_stop_behavior() -> None:
    assert ALERT_WRITE_RULES[AlertEventType.DANGEROUS_OBJECT_DETECTED] == AlertWriteRule(
        severity=AlertSeverity.CRITICAL,
        emergency_stop_triggered=True,
        description="Dangerous objects in the workspace must force an immediate stop.",
    )
    assert ALERT_WRITE_RULES[AlertEventType.VALIDATION_FAILED].severity is AlertSeverity.HIGH
    assert ALERT_WRITE_RULES[AlertEventType.VALIDATION_FAILED].emergency_stop_triggered is False
    assert ALERT_WRITE_RULES[AlertEventType.EXECUTION_FAILED].emergency_stop_triggered is True
    assert ALERT_WRITE_RULES[AlertEventType.EMERGENCY_STOPPED].severity is AlertSeverity.CRITICAL


def test_alert_escalation_rules_cover_mvp_failure_paths() -> None:
    escalation_map = {
        (rule.source_event_type, tuple(sorted(rule.source_outcomes, key=lambda item: item.value))): rule
        for rule in ALERT_ESCALATION_RULES
    }

    dangerous_rule = escalation_map[
        (AuditEventType.VISION_LOCATED, (AuditOutcome.EMERGENCY,))
    ]
    validation_rule = escalation_map[
        (AuditEventType.VALIDATION_COMPLETED, (AuditOutcome.FAILED,))
    ]
    execution_rule = escalation_map[
        (
            AuditEventType.ROBOT_EXECUTED,
            tuple(sorted((AuditOutcome.EMERGENCY, AuditOutcome.FAILED), key=lambda item: item.value)),
        )
    ]
    verification_rule = escalation_map[
        (AuditEventType.VISION_VERIFIED, (AuditOutcome.FAILED,))
    ]
    emergency_rule = escalation_map[
        (AuditEventType.TASK_STATUS_CHANGED, (AuditOutcome.EMERGENCY,))
    ]

    assert dangerous_rule.alert_event_type is AlertEventType.DANGEROUS_OBJECT_DETECTED
    assert validation_rule.alert_event_type is AlertEventType.VALIDATION_FAILED
    assert execution_rule.alert_event_type is AlertEventType.EXECUTION_FAILED
    assert verification_rule.alert_event_type is AlertEventType.VERIFICATION_FAILED
    assert emergency_rule.alert_event_type is AlertEventType.EMERGENCY_STOPPED


def test_audit_payload_guard_rejects_raw_chain_of_thought_keys_case_insensitively() -> None:
    payload = {
        "input_summary": {"instruction": "pick the part"},
        "nested": {
            "Raw Chain Of Thought": "hidden",
            "children": [{"internal-reasoning": "hidden"}],
        },
        "entries": [{"Scratchpad": "hidden"}],
    }

    forbidden_paths = find_forbidden_audit_payload_paths(payload)

    assert forbidden_paths == (
        "payload.nested.Raw Chain Of Thought",
        "payload.nested.children[0].internal-reasoning",
        "payload.entries[0].Scratchpad",
    )
    with pytest.raises(ValueError, match="forbidden raw reasoning fields"):
        assert_audit_payload_is_safe(payload)


def test_audit_payload_guard_allows_structured_summaries() -> None:
    payload = {
        "input_summary": {"instruction": "pick the part"},
        "context_sources": ["knowledge:sample-1", "prompt:planner-v1"],
        "output_summary": {"allowed_to_run": False},
    }

    assert find_forbidden_audit_payload_paths(payload) == ()
    assert_audit_payload_is_safe(payload)
