"""Initial PostgreSQL 16 schema with pgvector baseline tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import UserDefinedType


revision = "20260416_01"
down_revision = None
branch_labels = None
depends_on = None


class Vector(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int = 1536) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **_: object) -> str:
        return f"vector({self.dimensions})"


def _enum(name: str, values: list[str]) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=True)


TASK_TYPE_ENUM = _enum("task_type_enum", ["pick_and_place"])
TASK_STATUS_ENUM = _enum(
    "task_status_enum",
    [
        "created",
        "planning",
        "validating",
        "ready_to_run",
        "running",
        "verifying",
        "succeeded",
        "failed",
        "emergency_stopped",
    ],
)
TASK_FAILURE_CATEGORY_ENUM = _enum(
    "task_failure_category_enum",
    [
        "incomplete_input",
        "object_not_found",
        "dangerous_object_detected",
        "workspace_violation",
        "validation_failed",
        "collision_risk",
        "execution_interrupted",
        "grasp_slip",
        "verification_failed",
        "planning_exhausted",
        "emergency_stopped",
    ],
)
MODULE_NAME_ENUM = _enum(
    "module_name_enum",
    [
        "web_console",
        "api_server",
        "executor_worker",
        "task_service",
        "knowledge_memory",
        "vision",
        "planner",
        "coder",
        "critic",
        "robot_adapter",
        "audit_alert",
    ],
)
ROBOT_EXECUTION_STATUS_ENUM = _enum(
    "robot_execution_status_enum",
    [
        "Success",
        "Validation_Failed",
        "Collision_Detected",
        "Workspace_Violation",
        "Object_Not_Found",
        "Grasp_Slip",
        "Execution_Interrupted",
        "Emergency_Stop",
    ],
)
ALERT_SEVERITY_ENUM = _enum("alert_severity_enum", ["low", "medium", "high", "critical"])
ALERT_HANDLING_STATUS_ENUM = _enum(
    "alert_handling_status_enum", ["open", "acknowledged", "resolved"]
)
ALERT_EVENT_TYPE_ENUM = _enum(
    "alert_event_type_enum",
    [
        "dangerous_object_detected",
        "validation_failed",
        "execution_failed",
        "verification_failed",
        "emergency_stopped",
    ],
)
AUDIT_EVENT_TYPE_ENUM = _enum(
    "audit_event_type_enum",
    [
        "task_created",
        "task_status_changed",
        "knowledge_retrieved",
        "vision_located",
        "plan_generated",
        "script_generated",
        "validation_completed",
        "robot_executed",
        "vision_verified",
        "memory_written",
        "alert_created",
    ],
)
AUDIT_OUTCOME_ENUM = _enum("audit_outcome_enum", ["success", "failed", "emergency"])


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    bind = op.get_bind()
    for enum_type in (
        TASK_TYPE_ENUM,
        TASK_STATUS_ENUM,
        TASK_FAILURE_CATEGORY_ENUM,
        MODULE_NAME_ENUM,
        ROBOT_EXECUTION_STATUS_ENUM,
        ALERT_SEVERITY_ENUM,
        ALERT_HANDLING_STATUS_ENUM,
        ALERT_EVENT_TYPE_ENUM,
        AUDIT_EVENT_TYPE_ENUM,
        AUDIT_OUTCOME_ENUM,
    ):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("user_id", name="pk_users"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_is_active_deleted_at", "users", ["is_active", "deleted_at"], unique=False)

    op.create_table(
        "roles",
        sa.Column("role_id", sa.String(length=128), nullable=False),
        sa.Column("role_code", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("role_id", name="pk_roles"),
        sa.UniqueConstraint("role_code", name="uq_roles_role_code"),
    )
    op.create_index("ix_roles_is_active_deleted_at", "roles", ["is_active", "deleted_at"], unique=False)

    op.create_table(
        "artifact_references",
        sa.Column("artifact_id", sa.String(length=128), nullable=False),
        sa.Column("artifact_kind", sa.String(length=64), nullable=False),
        sa.Column("storage_backend", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("checksum_sha256", sa.String(length=255), nullable=True),
        sa.Column("byte_size", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("artifact_id", name="pk_artifact_references"),
    )
    op.create_index(
        "ix_artifact_references_storage_backend_deleted_at",
        "artifact_references",
        ["storage_backend", "deleted_at"],
        unique=False,
    )

    op.create_table(
        "robot_configs",
        sa.Column("robot_config_id", sa.String(length=128), nullable=False),
        sa.Column("robot_id", sa.String(length=128), nullable=False),
        sa.Column("vendor_name", sa.String(length=255), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("sdk_version", sa.String(length=255), nullable=True),
        sa.Column("connection_params", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("workspace_params", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("updated_by_user_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.user_id"], name="fk_robot_configs_updated_by_user_id_users", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("robot_config_id", name="pk_robot_configs"),
        sa.UniqueConstraint("robot_id", name="uq_robot_configs_robot_id"),
    )
    op.create_index("ix_robot_configs_is_active_deleted_at", "robot_configs", ["is_active", "deleted_at"], unique=False)

    op.create_table(
        "safety_rule_sets",
        sa.Column("safety_rule_set_id", sa.String(length=128), nullable=False),
        sa.Column("rule_set_name", sa.String(length=255), nullable=False),
        sa.Column("workspace_bounds", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("forbidden_zones", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("joint_limits", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("emergency_stop_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("max_task_duration_seconds", sa.Integer(), nullable=False, server_default=sa.text("60")),
        sa.Column("vision_confidence_threshold", sa.Numeric(4, 3), nullable=False, server_default=sa.text("0.7")),
        sa.Column("placement_tolerance_mm", sa.Numeric(10, 3), nullable=False, server_default=sa.text("5.0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("updated_by_user_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.user_id"], name="fk_safety_rule_sets_updated_by_user_id_users", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("safety_rule_set_id", name="pk_safety_rule_sets"),
        sa.UniqueConstraint("rule_set_name", name="uq_safety_rule_sets_rule_set_name"),
    )
    op.create_index("ix_safety_rule_sets_is_active_deleted_at", "safety_rule_sets", ["is_active", "deleted_at"], unique=False)

    op.create_table(
        "system_configs",
        sa.Column("system_config_id", sa.String(length=128), nullable=False),
        sa.Column("config_namespace", sa.String(length=64), nullable=False),
        sa.Column("config_key", sa.String(length=255), nullable=False),
        sa.Column("config_value", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("updated_by_user_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.user_id"], name="fk_system_configs_updated_by_user_id_users", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("system_config_id", name="pk_system_configs"),
        sa.UniqueConstraint("config_namespace", "config_key", name="uq_system_configs_config_namespace_config_key"),
    )
    op.create_index("ix_system_configs_namespace_deleted_at", "system_configs", ["config_namespace", "deleted_at"], unique=False)

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("role_id", sa.String(length=128), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"], name="fk_user_roles_role_id_roles", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_user_roles_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id", name="pk_user_roles"),
    )

    op.create_table(
        "sessions",
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("session_token_hash", sa.String(length=255), nullable=False),
        sa.Column("client_ip", sa.String(length=255), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_sessions_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("session_id", name="pk_sessions"),
        sa.UniqueConstraint("session_token_hash", name="uq_sessions_session_token_hash"),
    )
    op.create_index("ix_sessions_user_id_expires_at", "sessions", ["user_id", "expires_at"], unique=False)
    op.create_index("ix_sessions_revoked_at_expires_at", "sessions", ["revoked_at", "expires_at"], unique=False)

    op.create_table(
        "tasks",
        sa.Column("task_id", sa.String(length=128), nullable=False),
        sa.Column("task_type", TASK_TYPE_ENUM, nullable=False, server_default=sa.text("'pick_and_place'")),
        sa.Column("raw_instruction", sa.Text(), nullable=False),
        sa.Column("target_object", sa.String(length=255), nullable=False),
        sa.Column("target_location", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", TASK_STATUS_ENUM, nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("failure_category", TASK_FAILURE_CATEGORY_ENUM, nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("robot_id", sa.String(length=128), nullable=False),
        sa.Column("workstation_id", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("task_id", name="pk_tasks"),
    )
    op.create_index("ix_tasks_status_created_at", "tasks", ["status", "created_at"], unique=False)
    op.create_index("ix_tasks_robot_id_created_at", "tasks", ["robot_id", "created_at"], unique=False)
    op.create_index("ix_tasks_workstation_id_created_at", "tasks", ["workstation_id", "created_at"], unique=False)

    op.create_table(
        "semantic_action_plans",
        sa.Column("semantic_plan_id", sa.String(length=128), nullable=False),
        sa.Column("task_id", sa.String(length=128), nullable=False),
        sa.Column("steps", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("preconditions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("planning_notes", sa.Text(), nullable=True),
        sa.Column("planner_summary", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.task_id"], name="fk_semantic_action_plans_task_id_tasks", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("semantic_plan_id", name="pk_semantic_action_plans"),
    )
    op.create_index("ix_semantic_action_plans_task_id_generated_at", "semantic_action_plans", ["task_id", "generated_at"], unique=False)

    op.create_table(
        "knowledge_items",
        sa.Column("knowledge_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("version", sa.String(length=255), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("retrieval_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("primary_artifact_id", sa.String(length=128), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["primary_artifact_id"], ["artifact_references.artifact_id"], name="fk_knowledge_items_primary_artifact_id_artifact_references", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("knowledge_id", name="pk_knowledge_items"),
    )
    op.create_index("ix_knowledge_items_source_type_deleted_at", "knowledge_items", ["source_type", "deleted_at"], unique=False)
    op.create_index("ix_knowledge_items_retrieval_metadata_gin", "knowledge_items", ["retrieval_metadata"], unique=False, postgresql_using="gin")

    op.create_table(
        "teaching_samples",
        sa.Column("sample_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("task_type", TASK_TYPE_ENUM, nullable=True),
        sa.Column("target_object", sa.String(length=255), nullable=True),
        sa.Column("workstation_id", sa.String(length=128), nullable=True),
        sa.Column("robot_id", sa.String(length=128), nullable=True),
        sa.Column("success_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("sample_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("retrieval_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("primary_artifact_id", sa.String(length=128), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["primary_artifact_id"], ["artifact_references.artifact_id"], name="fk_teaching_samples_primary_artifact_id_artifact_references", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("sample_id", name="pk_teaching_samples"),
    )
    op.create_index(
        "ix_teaching_samples_task_type_target_object_workstation_id",
        "teaching_samples",
        ["task_type", "target_object", "workstation_id"],
        unique=False,
    )
    op.create_index("ix_teaching_samples_retrieval_metadata_gin", "teaching_samples", ["retrieval_metadata"], unique=False, postgresql_using="gin")

    op.create_table(
        "execution_plans",
        sa.Column("plan_id", sa.String(length=128), nullable=False),
        sa.Column("task_id", sa.String(length=128), nullable=False),
        sa.Column("semantic_plan_id", sa.String(length=128), nullable=False),
        sa.Column("steps", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("action_params", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("preconditions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("validation_result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("allowed_to_run", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("script_version", sa.String(length=255), nullable=True),
        sa.Column("script_artifact_id", sa.String(length=128), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["script_artifact_id"], ["artifact_references.artifact_id"], name="fk_execution_plans_script_artifact_id_artifact_references", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["semantic_plan_id"], ["semantic_action_plans.semantic_plan_id"], name="fk_execution_plans_semantic_plan_id_semantic_action_plans", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.task_id"], name="fk_execution_plans_task_id_tasks", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("plan_id", name="pk_execution_plans"),
    )
    op.create_index("ix_execution_plans_task_id_generated_at", "execution_plans", ["task_id", "generated_at"], unique=False)
    op.create_index("ix_execution_plans_allowed_to_run_generated_at", "execution_plans", ["allowed_to_run", "generated_at"], unique=False)

    op.create_table(
        "execution_results",
        sa.Column("execution_id", sa.String(length=128), nullable=False),
        sa.Column("task_id", sa.String(length=128), nullable=False),
        sa.Column("plan_id", sa.String(length=128), nullable=True),
        sa.Column("robot_status", ROBOT_EXECUTION_STATUS_ENUM, nullable=False),
        sa.Column("error_code", sa.String(length=255), nullable=True),
        sa.Column("vision_verification", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("memory_written", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("primary_artifact_id", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["execution_plans.plan_id"], name="fk_execution_results_plan_id_execution_plans", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["primary_artifact_id"], ["artifact_references.artifact_id"], name="fk_execution_results_primary_artifact_id_artifact_references", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.task_id"], name="fk_execution_results_task_id_tasks", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("execution_id", name="pk_execution_results"),
    )
    op.create_index("ix_execution_results_task_id_finished_at", "execution_results", ["task_id", "finished_at"], unique=False)
    op.create_index("ix_execution_results_robot_status_finished_at", "execution_results", ["robot_status", "finished_at"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("alert_id", sa.String(length=128), nullable=False),
        sa.Column("task_id", sa.String(length=128), nullable=True),
        sa.Column("event_type", ALERT_EVENT_TYPE_ENUM, nullable=False),
        sa.Column("severity", ALERT_SEVERITY_ENUM, nullable=False),
        sa.Column("trigger_module", MODULE_NAME_ENUM, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("handling_status", ALERT_HANDLING_STATUS_ENUM, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("emergency_stop_triggered", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.task_id"], name="fk_alerts_task_id_tasks", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("alert_id", name="pk_alerts"),
    )
    op.create_index("ix_alerts_task_id_occurred_at", "alerts", ["task_id", "occurred_at"], unique=False)
    op.create_index("ix_alerts_handling_status_occurred_at", "alerts", ["handling_status", "occurred_at"], unique=False)
    op.create_index("ix_alerts_severity_occurred_at", "alerts", ["severity", "occurred_at"], unique=False)

    op.create_table(
        "audit_records",
        sa.Column("audit_event_id", sa.String(length=128), nullable=False),
        sa.Column("task_id", sa.String(length=128), nullable=True),
        sa.Column("event_type", AUDIT_EVENT_TYPE_ENUM, nullable=False),
        sa.Column("source_module", MODULE_NAME_ENUM, nullable=False),
        sa.Column("outcome", AUDIT_OUTCOME_ENUM, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("status_from", TASK_STATUS_ENUM, nullable=True),
        sa.Column("status_to", TASK_STATUS_ENUM, nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.task_id"], name="fk_audit_records_task_id_tasks", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("audit_event_id", name="pk_audit_records"),
    )
    op.create_index("ix_audit_records_task_id_occurred_at", "audit_records", ["task_id", "occurred_at"], unique=False)
    op.create_index("ix_audit_records_source_module_occurred_at", "audit_records", ["source_module", "occurred_at"], unique=False)
    op.create_index("ix_audit_records_status_to_occurred_at", "audit_records", ["status_to", "occurred_at"], unique=False)

    op.create_table(
        "long_term_memories",
        sa.Column("memory_id", sa.String(length=128), nullable=False),
        sa.Column("task_id", sa.String(length=128), nullable=False),
        sa.Column("task_type", TASK_TYPE_ENUM, nullable=False),
        sa.Column("target_object", sa.String(length=255), nullable=False),
        sa.Column("workstation_id", sa.String(length=128), nullable=False),
        sa.Column("robot_id", sa.String(length=128), nullable=False),
        sa.Column("robot_config_id", sa.String(length=128), nullable=True),
        sa.Column("scene_label", sa.String(length=255), nullable=True),
        sa.Column("key_grasp_parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("placement_parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("retrieval_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("script_version", sa.String(length=255), nullable=False),
        sa.Column("vision_verification", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_label", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["robot_config_id"], ["robot_configs.robot_config_id"], name="fk_long_term_memories_robot_config_id_robot_configs", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.task_id"], name="fk_long_term_memories_task_id_tasks", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("memory_id", name="pk_long_term_memories"),
    )
    op.create_index("ix_long_term_memories_workstation_id_task_type_target_object", "long_term_memories", ["workstation_id", "task_type", "target_object"], unique=False)
    op.create_index("ix_long_term_memories_robot_id_recorded_at", "long_term_memories", ["robot_id", "recorded_at"], unique=False)
    op.create_index("ix_long_term_memories_retrieval_metadata_gin", "long_term_memories", ["retrieval_metadata"], unique=False, postgresql_using="gin")

    op.execute(
        "CREATE INDEX ix_knowledge_items_embedding_hnsw "
        "ON knowledge_items USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX ix_teaching_samples_embedding_hnsw "
        "ON teaching_samples USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX ix_long_term_memories_embedding_hnsw "
        "ON long_term_memories USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_long_term_memories_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_teaching_samples_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_items_embedding_hnsw")

    op.drop_table("long_term_memories")
    op.drop_table("audit_records")
    op.drop_table("alerts")
    op.drop_table("execution_results")
    op.drop_table("execution_plans")
    op.drop_table("teaching_samples")
    op.drop_table("knowledge_items")
    op.drop_table("semantic_action_plans")
    op.drop_table("tasks")
    op.drop_table("sessions")
    op.drop_table("user_roles")
    op.drop_table("system_configs")
    op.drop_table("safety_rule_sets")
    op.drop_table("robot_configs")
    op.drop_table("artifact_references")
    op.drop_table("roles")
    op.drop_table("users")

    bind = op.get_bind()
    for enum_type in (
        AUDIT_OUTCOME_ENUM,
        AUDIT_EVENT_TYPE_ENUM,
        ALERT_EVENT_TYPE_ENUM,
        ALERT_HANDLING_STATUS_ENUM,
        ALERT_SEVERITY_ENUM,
        ROBOT_EXECUTION_STATUS_ENUM,
        MODULE_NAME_ENUM,
        TASK_FAILURE_CATEGORY_ENUM,
        TASK_STATUS_ENUM,
        TASK_TYPE_ENUM,
    ):
        enum_type.drop(bind, checkfirst=True)
