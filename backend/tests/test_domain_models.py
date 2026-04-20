from __future__ import annotations

from datetime import datetime, timezone

from robot_control_backend.domain.enums import (
    AlertEventType,
    AlertHandlingStatus,
    AlertSeverity,
    AuditEventType,
    AuditOutcome,
    ModuleName,
    RobotExecutionStatus,
    TaskStatus,
)
from robot_control_backend.domain.models import (
    AlertRecord,
    AuditRecord,
    AuditEventRecord,
    CoderContext,
    CoderOutput,
    ControlledScript,
    ExecutionPlan,
    ExecutionResult,
    LongTermMemoryRecord,
    PlanStep,
    PlannerOutput,
    Pose3D,
    SemanticActionPlan,
    SemanticActionStep,
    ScriptStepBinding,
    TargetLocation,
    TaskRecord,
    ValidationResult,
    VisionVerificationResult,
)


def test_task_plan_execution_and_trace_models_cover_minimum_fields() -> None:
    timestamp = datetime.now(timezone.utc)
    pose = Pose3D(
        frame_id="robot_base",
        x_mm=100.0,
        y_mm=50.0,
        z_mm=25.0,
        rz_deg=90.0,
    )
    location = TargetLocation(
        station_id="station-a",
        slot_id="tray-b-1",
        pose=pose,
    )
    task = TaskRecord(
        task_id="task-001",
        raw_instruction="将工位 A 上的零件抓取并放到托盘 B 的指定位置",
        target_object="part",
        target_location=location,
        status=TaskStatus.CREATED,
        created_by="operator-1",
        created_at=timestamp,
        robot_id="robot-1",
        workstation_id="workstation-1",
    )
    semantic_plan = SemanticActionPlan(
        semantic_plan_id="semantic-plan-001",
        task_id=task.task_id,
        steps=[
            SemanticActionStep(
                step_id="semantic-step-1",
                sequence=1,
                semantic_action="locate_target",
                description="定位目标物",
                expected_outcome="得到可用于执行绑定的目标物位姿",
            )
        ],
        generated_at=timestamp,
    )
    plan = ExecutionPlan(
        plan_id="plan-001",
        task_id=task.task_id,
        semantic_plan_id=semantic_plan.semantic_plan_id,
        steps=[
            PlanStep(
                step_id="step-1",
                sequence=1,
                action_name="locate_target",
                description="定位目标物",
                expected_outcome="得到目标坐标",
            )
        ],
        validation_result=ValidationResult(allowed_to_run=False),
    )
    planner_output = PlannerOutput(
        semantic_action_plan=semantic_plan,
        planner_summary="已生成语义动作计划",
    )
    coder_context = CoderContext(task=task, semantic_action_plan=semantic_plan)
    controlled_script = ControlledScript(
        script_id="script-001",
        task_id=task.task_id,
        plan_id=plan.plan_id,
        script_version="script-v1",
        template_version="template-v1",
        generated_at=timestamp,
        step_bindings=[
            ScriptStepBinding(
                step_id="step-1",
                template_name="locate_target_template",
                parameters={"vision_capture_required": True},
            )
        ],
    )
    coder_output = CoderOutput(
        execution_plan=plan,
        controlled_script=controlled_script,
        script_summary="已生成受控脚本摘要",
    )
    verification = VisionVerificationResult(
        task_id=task.task_id,
        verified=True,
        confidence=0.92,
        expected_pose=pose,
        observed_pose=pose,
        deviation_mm=0.8,
        captured_at=timestamp,
    )
    execution = ExecutionResult(
        execution_id="exec-001",
        task_id=task.task_id,
        robot_status=RobotExecutionStatus.SUCCESS,
        vision_verification=verification,
        memory_written=True,
        finished_at=timestamp,
    )
    alert = AlertRecord(
        alert_id="alert-001",
        task_id=task.task_id,
        related_audit_event_id="audit-001",
        event_type=AlertEventType.VALIDATION_FAILED,
        severity=AlertSeverity.HIGH,
        trigger_module=ModuleName.CRITIC,
        message="校验失败",
        handling_status=AlertHandlingStatus.OPEN,
        occurred_at=timestamp,
    )
    audit_event = AuditRecord(
        audit_event_id="audit-001",
        task_id=task.task_id,
        event_type=AuditEventType.TASK_STATUS_CHANGED,
        source_module=ModuleName.EXECUTOR_WORKER,
        outcome=AuditOutcome.SUCCESS,
        occurred_at=timestamp,
        summary="任务状态切换到 validating",
        status_from=TaskStatus.PLANNING,
        status_to=TaskStatus.VALIDATING,
    )
    memory = LongTermMemoryRecord(
        memory_id="memory-001",
        task_id=task.task_id,
        task_type=task.task_type,
        target_object=task.target_object,
        key_grasp_parameters={"approach_height_mm": 40},
        placement_parameters={"drop_height_mm": 8},
        script_version="script-v1",
        vision_verification=verification,
        recorded_at=timestamp,
        source_label="live_run",
    )

    assert task.task_id == "task-001"
    assert planner_output.semantic_action_plan is not None
    assert coder_context.semantic_action_plan.semantic_plan_id == semantic_plan.semantic_plan_id
    assert coder_output.execution_plan.semantic_plan_id == semantic_plan.semantic_plan_id
    assert plan.steps[0].action_name == "locate_target"
    assert execution.memory_written is True
    assert alert.trigger_module is ModuleName.CRITIC
    assert alert.related_audit_event_id == "audit-001"
    assert audit_event.status_to is TaskStatus.VALIDATING
    assert memory.vision_verification.verified is True


def test_audit_record_backward_compatibility_alias_is_preserved() -> None:
    assert AuditEventRecord is AuditRecord
