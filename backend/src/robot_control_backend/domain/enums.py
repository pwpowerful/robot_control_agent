from __future__ import annotations

from enum import Enum


class TaskType(str, Enum):
    """Supported task type set for the current MVP."""

    PICK_AND_PLACE = "pick_and_place"


class TaskStatus(str, Enum):
    """Unified task lifecycle statuses shared by all modules."""

    CREATED = "created"
    PLANNING = "planning"
    VALIDATING = "validating"
    READY_TO_RUN = "ready_to_run"
    RUNNING = "running"
    VERIFYING = "verifying"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    EMERGENCY_STOPPED = "emergency_stopped"


class TaskFailureCategory(str, Enum):
    """Business-level failure categories persisted on tasks."""

    INCOMPLETE_INPUT = "incomplete_input"
    OBJECT_NOT_FOUND = "object_not_found"
    DANGEROUS_OBJECT_DETECTED = "dangerous_object_detected"
    WORKSPACE_VIOLATION = "workspace_violation"
    VALIDATION_FAILED = "validation_failed"
    COLLISION_RISK = "collision_risk"
    EXECUTION_INTERRUPTED = "execution_interrupted"
    GRASP_SLIP = "grasp_slip"
    VERIFICATION_FAILED = "verification_failed"
    PLANNING_EXHAUSTED = "planning_exhausted"
    EMERGENCY_STOPPED = "emergency_stopped"


class ValidationFailureCategory(str, Enum):
    """Failure categories returned by Critic validation."""

    SYNTAX_INVALID = "syntax_invalid"
    NON_WHITELISTED_ACTION = "non_whitelisted_action"
    JOINT_LIMIT_EXCEEDED = "joint_limit_exceeded"
    REACHABILITY_FAILED = "reachability_failed"
    WORKSPACE_VIOLATION = "workspace_violation"
    COLLISION_RISK = "collision_risk"
    GRIPPER_PHASE_VIOLATION = "gripper_phase_violation"
    RETRY_LIMIT_REACHED = "retry_limit_reached"


class ModuleName(str, Enum):
    """Canonical module names shared across audit, alerts, and contracts."""

    WEB_CONSOLE = "web_console"
    API_SERVER = "api_server"
    EXECUTOR_WORKER = "executor_worker"
    TASK_SERVICE = "task_service"
    KNOWLEDGE_MEMORY = "knowledge_memory"
    VISION = "vision"
    PLANNER = "planner"
    CODER = "coder"
    CRITIC = "critic"
    ROBOT_ADAPTER = "robot_adapter"
    AUDIT_ALERT = "audit_alert"


class RobotExecutionStatus(str, Enum):
    """Normalized robot adapter statuses from the design document."""

    SUCCESS = "Success"
    VALIDATION_FAILED = "Validation_Failed"
    COLLISION_DETECTED = "Collision_Detected"
    WORKSPACE_VIOLATION = "Workspace_Violation"
    OBJECT_NOT_FOUND = "Object_Not_Found"
    GRASP_SLIP = "Grasp_Slip"
    EXECUTION_INTERRUPTED = "Execution_Interrupted"
    EMERGENCY_STOP = "Emergency_Stop"


class AlertSeverity(str, Enum):
    """Alert severity levels visible in the console."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertHandlingStatus(str, Enum):
    """Alert handling state used by the alert center."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertEventType(str, Enum):
    """Alert event categories required by the MVP failure flow."""

    DANGEROUS_OBJECT_DETECTED = "dangerous_object_detected"
    VALIDATION_FAILED = "validation_failed"
    EXECUTION_FAILED = "execution_failed"
    VERIFICATION_FAILED = "verification_failed"
    EMERGENCY_STOPPED = "emergency_stopped"


class AuditEventType(str, Enum):
    """Audit event types needed for full-chain traceability."""

    TASK_CREATED = "task_created"
    CONTEXT_ASSEMBLED = "context_assembled"
    TASK_STATUS_CHANGED = "task_status_changed"
    KNOWLEDGE_RETRIEVED = "knowledge_retrieved"
    TOOL_CALLED = "tool_called"
    VISION_LOCATED = "vision_located"
    AGENT_OUTPUT_RECORDED = "agent_output_recorded"
    PLAN_GENERATED = "plan_generated"
    SCRIPT_GENERATED = "script_generated"
    VALIDATION_COMPLETED = "validation_completed"
    ROBOT_EXECUTED = "robot_executed"
    VISION_VERIFIED = "vision_verified"
    MEMORY_WRITTEN = "memory_written"
    ALERT_CREATED = "alert_created"


class AuditOutcome(str, Enum):
    """Audit event result classification."""

    SUCCESS = "success"
    FAILED = "failed"
    EMERGENCY = "emergency"
