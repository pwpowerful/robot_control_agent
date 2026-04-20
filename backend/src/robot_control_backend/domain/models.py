from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from robot_control_backend.domain.enums import (
    AlertEventType,
    AlertHandlingStatus,
    AlertSeverity,
    AuditEventType,
    AuditOutcome,
    ModuleName,
    RobotExecutionStatus,
    TaskFailureCategory,
    TaskStatus,
    TaskType,
    ValidationFailureCategory,
)


class DomainModel(BaseModel):
    """Base class for shared DTOs passed between backend modules."""

    model_config = ConfigDict(extra="forbid")


class Pose3D(DomainModel):
    """Physical pose expressed in a named coordinate frame."""

    frame_id: str = Field(description="Coordinate frame identifier such as robot_base or camera.")
    x_mm: float = Field(description="X position in millimeters.")
    y_mm: float = Field(description="Y position in millimeters.")
    z_mm: float = Field(description="Z position in millimeters.")
    rx_deg: float | None = Field(default=None, description="Rotation around X axis in degrees.")
    ry_deg: float | None = Field(default=None, description="Rotation around Y axis in degrees.")
    rz_deg: float | None = Field(default=None, description="Rotation around Z axis in degrees.")


class TargetLocation(DomainModel):
    """Target placement location extracted from the task request."""

    station_id: str = Field(description="Business workstation or station identifier.")
    slot_id: str | None = Field(default=None, description="Placement slot or named target position.")
    pose: Pose3D = Field(description="Expected target pose in the robot coordinate space.")
    tolerance_mm: float = Field(default=5.0, description="Placement tolerance in millimeters.")


class DetectedObject(DomainModel):
    """Structured object detection result shared by Vision and Planner."""

    object_type: str = Field(description="Detected object semantic type.")
    object_id: str | None = Field(default=None, description="Optional object instance identifier.")
    confidence: float = Field(description="Detection confidence score between 0 and 1.")
    pose: Pose3D | None = Field(
        default=None,
        description="Detected object pose when the object can be mapped to robot coordinates.",
    )


class KnowledgeReference(DomainModel):
    """Retrieved knowledge item metadata used during planning."""

    knowledge_id: str = Field(description="Knowledge item identifier.")
    title: str = Field(description="Display title of the knowledge item.")
    source_type: str = Field(description="Source type such as sdk_document or sop.")
    summary: str = Field(description="Short summary passed into downstream planning modules.")
    version: str | None = Field(default=None, description="Source version label if available.")


class TeachingSampleReference(DomainModel):
    """Retrieved teaching sample metadata used during planning."""

    sample_id: str = Field(description="Teaching sample identifier.")
    title: str = Field(description="Display title of the teaching sample.")
    summary: str = Field(description="Short summary of the sample outcome and applicability.")
    robot_id: str | None = Field(default=None, description="Robot identifier associated with the sample.")
    success_rate: float | None = Field(default=None, description="Optional historical success rate.")


class KnowledgeContextBundle(DomainModel):
    """Bundle of knowledge and teaching samples handed to Planner."""

    task_id: str = Field(description="Task identifier that triggered retrieval.")
    knowledge_items: list[KnowledgeReference] = Field(
        default_factory=list,
        description="Retrieved knowledge items relevant to the current task.",
    )
    teaching_samples: list[TeachingSampleReference] = Field(
        default_factory=list,
        description="Retrieved teaching samples relevant to the current task.",
    )
    retrieved_at: datetime = Field(description="Timestamp when retrieval completed.")


class VisionLocateResult(DomainModel):
    """Pre-execution vision result used by Planner."""

    task_id: str = Field(description="Task identifier.")
    capture_id: str = Field(description="Vision capture identifier.")
    target_object: str = Field(description="Requested target object type.")
    target_found: bool = Field(description="Whether the target object was successfully located.")
    target_pose: Pose3D | None = Field(
        default=None,
        description="Resolved target pose if the target was found.",
    )
    located_objects: list[DetectedObject] = Field(
        default_factory=list,
        description="Structured list of located objects in the scene.",
    )
    dangerous_objects: list[DetectedObject] = Field(
        default_factory=list,
        description="Dangerous detections such as human hands in the workspace.",
    )
    capture_timestamp: datetime = Field(description="Timestamp of the frame or scene capture.")


class PlanPrecondition(DomainModel):
    """Precondition that must hold before a plan or step can run."""

    code: str = Field(description="Stable precondition code.")
    description: str = Field(description="Human-readable precondition description.")
    source_module: ModuleName = Field(description="Module that asserted this precondition.")


class ActionParameterSet(DomainModel):
    """Named action parameter payload associated with a planned step."""

    step_id: str = Field(description="Plan step identifier that consumes this parameter set.")
    parameter_source: ModuleName = Field(description="Module that produced the parameters.")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured action parameters consumed by controlled templates.",
    )


class PlanStep(DomainModel):
    """Controlled step in a pick-and-place execution plan."""

    step_id: str = Field(description="Unique step identifier within the plan.")
    sequence: int = Field(description="Execution order within the plan.")
    action_name: str = Field(description="Whitelisted action or template name.")
    description: str = Field(description="Human-readable step description.")
    expected_outcome: str = Field(description="Expected step result used for auditing and debugging.")
    preconditions: list[str] = Field(
        default_factory=list,
        description="Precondition codes required before this step can run.",
    )


class SemanticActionStep(DomainModel):
    """Task-level semantic step produced by Planner before execution binding."""

    step_id: str = Field(description="Unique step identifier within the semantic plan.")
    sequence: int = Field(description="Execution order within the semantic plan.")
    semantic_action: str = Field(description="Semantic action name such as locate_target or transfer_target.")
    description: str = Field(description="Human-readable semantic step description.")
    expected_outcome: str = Field(description="Expected semantic result before execution binding.")


class ValidationFinding(DomainModel):
    """Single validation finding emitted by Critic."""

    code: str = Field(description="Stable validation rule or finding code.")
    severity: AlertSeverity = Field(description="Severity of the finding.")
    description: str = Field(description="Human-readable validation message.")
    step_id: str | None = Field(default=None, description="Related plan step identifier if applicable.")
    source_module: ModuleName = Field(default=ModuleName.CRITIC, description="Producing module name.")


class ValidationResult(DomainModel):
    """Structured validation result returned by Critic."""

    allowed_to_run: bool = Field(description="Whether the validated content may enter execution.")
    failure_category: ValidationFailureCategory | None = Field(
        default=None,
        description="Validation failure category when execution is rejected.",
    )
    failure_description: str | None = Field(
        default=None,
        description="Human-readable failure summary used in task details and alerts.",
    )
    related_step_id: str | None = Field(
        default=None,
        description="Plan step most closely associated with the failure.",
    )
    suggested_return_module: ModuleName | None = Field(
        default=None,
        description="Module to revisit when validation fails and retry is still allowed.",
    )
    findings: list[ValidationFinding] = Field(
        default_factory=list,
        description="Detailed validation findings for audit and debugging.",
    )
    validated_at: datetime | None = Field(default=None, description="Validation completion timestamp.")


class ExecutionPlan(DomainModel):
    """Structured execution plan shared across Planner, Coder, Critic, and the task UI."""

    plan_id: str = Field(description="Execution plan identifier.")
    task_id: str = Field(description="Associated task identifier.")
    semantic_plan_id: str = Field(description="Associated semantic action plan identifier.")
    steps: list[PlanStep] = Field(description="Ordered controlled execution steps.")
    action_params: list[ActionParameterSet] = Field(
        default_factory=list,
        description="Parameter payloads used by the controlled steps.",
    )
    preconditions: list[PlanPrecondition] = Field(
        default_factory=list,
        description="Plan-level preconditions that must hold before execution.",
    )
    validation_result: ValidationResult | None = Field(
        default=None,
        description="Most recent Critic validation result attached to the plan.",
    )
    allowed_to_run: bool = Field(
        default=False,
        description="Normalized flag for whether execution is currently allowed.",
    )
    script_version: str | None = Field(
        default=None,
        description="Coder-generated script version linked back to this plan.",
    )


class SemanticActionPlan(DomainModel):
    """Planner output that expresses task-level semantic steps before execution binding."""

    semantic_plan_id: str = Field(description="Semantic action plan identifier.")
    task_id: str = Field(description="Associated task identifier.")
    steps: list[SemanticActionStep] = Field(
        description="Ordered semantic action steps produced by Planner.",
    )
    preconditions: list[PlanPrecondition] = Field(
        default_factory=list,
        description="Plan-level semantic preconditions required before execution binding.",
    )
    planning_notes: str | None = Field(
        default=None,
        description="Optional Planner notes for audit and task-detail display.",
    )
    generated_at: datetime | None = Field(
        default=None,
        description="Semantic planning completion timestamp.",
    )


class TaskRecord(DomainModel):
    """Task record shared between API, worker, and the Web console."""

    task_id: str = Field(description="Task identifier.")
    task_type: TaskType = Field(default=TaskType.PICK_AND_PLACE, description="Normalized task type.")
    raw_instruction: str = Field(description="Original natural-language instruction.")
    target_object: str = Field(description="Requested target object.")
    target_location: TargetLocation = Field(description="Requested target placement location.")
    status: TaskStatus = Field(description="Current task lifecycle status.")
    failure_reason: str | None = Field(default=None, description="Latest human-readable failure reason.")
    failure_category: TaskFailureCategory | None = Field(
        default=None,
        description="Latest normalized failure category if the task failed.",
    )
    created_by: str = Field(description="Operator or user identifier that created the task.")
    created_at: datetime = Field(description="Task creation timestamp.")
    robot_id: str = Field(description="Active robot identifier for the task.")
    workstation_id: str = Field(description="Single-workstation identifier hosting the task.")


class PlannerContext(DomainModel):
    """Input bundle consumed by Planner."""

    task: TaskRecord = Field(description="Current task record.")
    vision_result: VisionLocateResult = Field(description="Pre-execution vision output.")
    knowledge_context: KnowledgeContextBundle = Field(description="Retrieved knowledge bundle.")
    safety_rule_set_id: str = Field(description="Active safety rule set identifier.")


class PlannerOutput(DomainModel):
    """Planner result passed to downstream modules."""

    semantic_action_plan: SemanticActionPlan | None = Field(
        default=None,
        description="Generated semantic action plan when planning succeeds.",
    )
    planner_summary: str = Field(description="Human-readable planning summary.")
    failure_reason: str | None = Field(
        default=None,
        description="Failure reason when planning cannot produce a valid plan.",
    )


class ScriptStepBinding(DomainModel):
    """Mapping between a plan step and a controlled execution template."""

    step_id: str = Field(description="Referenced plan step identifier.")
    template_name: str = Field(description="Controlled template name used by Coder.")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Resolved template parameters emitted by Coder.",
    )


class ControlledScript(DomainModel):
    """Controlled script summary produced by Coder."""

    script_id: str = Field(description="Controlled script identifier.")
    task_id: str = Field(description="Associated task identifier.")
    plan_id: str = Field(description="Associated plan identifier.")
    script_version: str = Field(description="Version label shown in audit and task details.")
    template_version: str = Field(description="Controlled template library version.")
    generated_at: datetime = Field(description="Script generation timestamp.")
    generated_by: ModuleName = Field(default=ModuleName.CODER, description="Producing module name.")
    step_bindings: list[ScriptStepBinding] = Field(
        default_factory=list,
        description="Template bindings that preserve traceability from plan to script.",
    )


class CoderContext(DomainModel):
    """Input bundle consumed by Coder."""

    task: TaskRecord = Field(description="Current task record.")
    semantic_action_plan: SemanticActionPlan = Field(
        description="Semantic action plan to translate into execution plan and controlled script form."
    )


class CoderOutput(DomainModel):
    """Coder output consumed by Critic and the task detail view."""

    execution_plan: ExecutionPlan = Field(
        description="Execution-level structured plan generated from the semantic action plan."
    )
    controlled_script: ControlledScript = Field(description="Generated controlled script summary.")
    script_summary: str = Field(description="Human-readable script generation summary.")


class CriticContext(DomainModel):
    """Input bundle consumed by Critic."""

    task: TaskRecord = Field(description="Current task record.")
    plan: ExecutionPlan = Field(description="Plan under validation.")
    controlled_script: ControlledScript = Field(description="Controlled script summary under validation.")


class RobotExecutionRequest(DomainModel):
    """Request handed from Worker to Robot adapter after validation passes."""

    task_id: str = Field(description="Task identifier.")
    plan_id: str = Field(description="Plan identifier.")
    script_version: str = Field(description="Controlled script version to execute.")
    step_bindings: list[ScriptStepBinding] = Field(
        default_factory=list,
        description="Resolved controlled step bindings executed by the adapter.",
    )
    requested_at: datetime = Field(description="Dispatch timestamp.")


class VisionVerificationResult(DomainModel):
    """Post-execution vision verification result."""

    task_id: str = Field(description="Task identifier.")
    verified: bool = Field(description="Whether the final placement was accepted.")
    confidence: float = Field(description="Verification confidence score between 0 and 1.")
    expected_pose: Pose3D | None = Field(default=None, description="Expected target pose after execution.")
    observed_pose: Pose3D | None = Field(default=None, description="Observed target pose after execution.")
    deviation_mm: float | None = Field(default=None, description="Observed deviation from expected pose.")
    tolerance_mm: float = Field(default=5.0, description="Allowed placement tolerance in millimeters.")
    captured_at: datetime = Field(description="Verification capture timestamp.")
    failure_reason: str | None = Field(default=None, description="Failure reason when verification fails.")


class ExecutionResult(DomainModel):
    """Execution result returned by Robot and enriched by post-run verification."""

    execution_id: str = Field(description="Execution record identifier.")
    task_id: str = Field(description="Associated task identifier.")
    robot_status: RobotExecutionStatus = Field(description="Normalized robot execution status.")
    error_code: str | None = Field(default=None, description="Normalized low-level error code if present.")
    vision_verification: VisionVerificationResult | None = Field(
        default=None,
        description="Post-execution vision verification result.",
    )
    memory_written: bool = Field(description="Whether a long-term memory record was written.")
    started_at: datetime | None = Field(default=None, description="Execution start timestamp.")
    finished_at: datetime = Field(description="Execution completion timestamp.")
    failure_reason: str | None = Field(default=None, description="Execution failure summary if present.")


class AlertRecord(DomainModel):
    """Alert event shown in the alert center."""

    alert_id: str = Field(description="Alert identifier.")
    task_id: str | None = Field(default=None, description="Associated task identifier if applicable.")
    related_audit_event_id: str | None = Field(
        default=None,
        description="Primary audit event identifier that explains why the alert was created.",
    )
    event_type: AlertEventType = Field(description="Alert event type.")
    severity: AlertSeverity = Field(description="Alert severity level.")
    trigger_module: ModuleName = Field(description="Module that triggered the alert.")
    message: str = Field(description="Human-readable alert message.")
    handling_status: AlertHandlingStatus = Field(description="Current alert handling status.")
    occurred_at: datetime = Field(description="Alert occurrence timestamp.")
    emergency_stop_triggered: bool = Field(
        default=False,
        description="Whether the alert forced an emergency stop.",
    )


class AuditRecord(DomainModel):
    """Audit event used for full-chain traceability."""

    audit_event_id: str = Field(description="Audit event identifier.")
    task_id: str | None = Field(default=None, description="Associated task identifier if applicable.")
    event_type: AuditEventType = Field(description="Audit event type.")
    source_module: ModuleName = Field(description="Module that emitted the event.")
    outcome: AuditOutcome = Field(description="Outcome of the audited action.")
    occurred_at: datetime = Field(description="Audit event timestamp.")
    summary: str = Field(description="Human-readable event summary.")
    actor_id: str | None = Field(default=None, description="User or system actor identifier if available.")
    status_from: TaskStatus | None = Field(default=None, description="Previous task status if changed.")
    status_to: TaskStatus | None = Field(default=None, description="New task status if changed.")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured event payload for replay and troubleshooting.",
    )


# Backward-compatible alias kept while the rest of the codebase migrates to the canonical name.
AuditEventRecord = AuditRecord


class MemoryWriteCandidate(DomainModel):
    """Structured memory candidate built before the final write decision."""

    task_id: str = Field(description="Associated task identifier.")
    task_type: TaskType = Field(description="Task type for future retrieval.")
    target_object: str = Field(description="Target object type.")
    key_grasp_parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Key parameters that influenced grasp success.",
    )
    placement_parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Key parameters that influenced placement success.",
    )
    script_version: str = Field(description="Controlled script version tied to the experience.")
    vision_verification: VisionVerificationResult = Field(
        description="Verification result that gates whether the memory can be written.",
    )
    source_label: str = Field(description="Source label such as live_run or teaching_sample.")


class LongTermMemoryRecord(DomainModel):
    """Persisted long-term memory record written only after successful verification."""

    memory_id: str = Field(description="Long-term memory identifier.")
    task_id: str = Field(description="Associated task identifier.")
    task_type: TaskType = Field(description="Task type for future retrieval.")
    target_object: str = Field(description="Target object type.")
    key_grasp_parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Persisted grasp parameters.",
    )
    placement_parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Persisted placement parameters.",
    )
    script_version: str = Field(description="Controlled script version associated with the success.")
    vision_verification: VisionVerificationResult = Field(
        description="Verification result proving the task outcome succeeded.",
    )
    recorded_at: datetime = Field(description="Memory persistence timestamp.")
    source_label: str = Field(description="Source label used for later traceability.")
