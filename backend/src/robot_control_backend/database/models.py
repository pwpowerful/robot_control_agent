from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from robot_control_backend.database.base import Base, SoftDeleteMixin, TimestampMixin
from robot_control_backend.database.types import DEFAULT_VECTOR_DIMENSIONS, Vector, sql_enum
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
)

STRING_ID_LENGTH = 128
NAME_LENGTH = 255
SHORT_CODE_LENGTH = 64


class UserModel(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        sa.UniqueConstraint("username"),
        sa.Index("ix_users_is_active_deleted_at", "is_active", "deleted_at"),
    )

    user_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), primary_key=True)
    username: Mapped[str] = mapped_column(sa.String(NAME_LENGTH), nullable=False)
    display_name: Mapped[str] = mapped_column(sa.String(NAME_LENGTH), nullable=False)
    password_hash: Mapped[str] = mapped_column(sa.String(NAME_LENGTH), nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean(), nullable=False, server_default=sa.true())


class RoleModel(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        sa.UniqueConstraint("role_code"),
        sa.Index("ix_roles_is_active_deleted_at", "is_active", "deleted_at"),
    )

    role_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), primary_key=True)
    role_code: Mapped[str] = mapped_column(sa.String(SHORT_CODE_LENGTH), nullable=False)
    display_name: Mapped[str] = mapped_column(sa.String(NAME_LENGTH), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    is_active: Mapped[bool] = mapped_column(sa.Boolean(), nullable=False, server_default=sa.true())


class UserRoleModel(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[str] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[str] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("roles.role_id", ondelete="CASCADE"),
        primary_key=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )


class SessionModel(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        sa.UniqueConstraint("session_token_hash"),
        sa.Index("ix_sessions_user_id_expires_at", "user_id", "expires_at"),
        sa.Index("ix_sessions_revoked_at_expires_at", "revoked_at", "expires_at"),
    )

    session_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    session_token_hash: Mapped[str] = mapped_column(sa.String(NAME_LENGTH), nullable=False)
    client_ip: Mapped[str | None] = mapped_column(sa.String(NAME_LENGTH), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)


class ArtifactReferenceModel(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "artifact_references"
    __table_args__ = (
        sa.Index("ix_artifact_references_storage_backend_deleted_at", "storage_backend", "deleted_at"),
    )

    artifact_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), primary_key=True)
    artifact_kind: Mapped[str] = mapped_column(sa.String(SHORT_CODE_LENGTH), nullable=False)
    storage_backend: Mapped[str] = mapped_column(sa.String(SHORT_CODE_LENGTH), nullable=False)
    storage_path: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    content_type: Mapped[str | None] = mapped_column(sa.String(NAME_LENGTH), nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(sa.String(NAME_LENGTH), nullable=True)
    byte_size: Mapped[int | None] = mapped_column(sa.BigInteger(), nullable=True)


class RobotConfigModel(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "robot_configs"
    __table_args__ = (
        sa.UniqueConstraint("robot_id"),
        sa.Index("ix_robot_configs_is_active_deleted_at", "is_active", "deleted_at"),
    )

    robot_config_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), primary_key=True)
    robot_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), nullable=False)
    vendor_name: Mapped[str] = mapped_column(sa.String(NAME_LENGTH), nullable=False)
    model_name: Mapped[str] = mapped_column(sa.String(NAME_LENGTH), nullable=False)
    sdk_version: Mapped[str | None] = mapped_column(sa.String(NAME_LENGTH), nullable=True)
    connection_params: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
    )
    workspace_params: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean(), nullable=False, server_default=sa.true())
    updated_by_user_id: Mapped[str | None] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )


class SafetyRuleSetModel(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "safety_rule_sets"
    __table_args__ = (
        sa.UniqueConstraint("rule_set_name"),
        sa.Index("ix_safety_rule_sets_is_active_deleted_at", "is_active", "deleted_at"),
    )

    safety_rule_set_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), primary_key=True)
    rule_set_name: Mapped[str] = mapped_column(sa.String(NAME_LENGTH), nullable=False)
    workspace_bounds: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
    )
    forbidden_zones: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=sa.text("'[]'::jsonb"),
    )
    joint_limits: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
    )
    emergency_stop_enabled: Mapped[bool] = mapped_column(
        sa.Boolean(),
        nullable=False,
        server_default=sa.true(),
    )
    max_task_duration_seconds: Mapped[int] = mapped_column(
        sa.Integer(),
        nullable=False,
        server_default=sa.text("60"),
    )
    vision_confidence_threshold: Mapped[Decimal] = mapped_column(
        sa.Numeric(4, 3),
        nullable=False,
        server_default=sa.text("0.7"),
    )
    placement_tolerance_mm: Mapped[Decimal] = mapped_column(
        sa.Numeric(10, 3),
        nullable=False,
        server_default=sa.text("5.0"),
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean(), nullable=False, server_default=sa.true())
    updated_by_user_id: Mapped[str | None] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )


class SystemConfigModel(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "system_configs"
    __table_args__ = (
        sa.UniqueConstraint("config_namespace", "config_key"),
        sa.Index("ix_system_configs_namespace_deleted_at", "config_namespace", "deleted_at"),
    )

    system_config_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), primary_key=True)
    config_namespace: Mapped[str] = mapped_column(sa.String(SHORT_CODE_LENGTH), nullable=False)
    config_key: Mapped[str] = mapped_column(sa.String(NAME_LENGTH), nullable=False)
    config_value: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
    )
    description: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    updated_by_user_id: Mapped[str | None] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )


class TaskModel(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        sa.Index("ix_tasks_status_created_at", "status", "created_at"),
        sa.Index("ix_tasks_robot_id_created_at", "robot_id", "created_at"),
        sa.Index("ix_tasks_workstation_id_created_at", "workstation_id", "created_at"),
    )

    task_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), primary_key=True)
    task_type: Mapped[TaskType] = mapped_column(
        sql_enum(TaskType, "task_type_enum"),
        nullable=False,
        server_default=sa.text("'pick_and_place'"),
    )
    raw_instruction: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    target_object: Mapped[str] = mapped_column(sa.String(NAME_LENGTH), nullable=False)
    target_location: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(sql_enum(TaskStatus, "task_status_enum"), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    failure_category: Mapped[TaskFailureCategory | None] = mapped_column(
        sql_enum(TaskFailureCategory, "task_failure_category_enum"),
        nullable=True,
    )
    created_by: Mapped[str] = mapped_column(sa.String(NAME_LENGTH), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    robot_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), nullable=False)
    workstation_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), nullable=False)


class SemanticActionPlanModel(Base):
    __tablename__ = "semantic_action_plans"
    __table_args__ = (
        sa.Index("ix_semantic_action_plans_task_id_generated_at", "task_id", "generated_at"),
    )

    semantic_plan_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), primary_key=True)
    task_id: Mapped[str] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("tasks.task_id", ondelete="CASCADE"),
        nullable=False,
    )
    steps: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    preconditions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=sa.text("'[]'::jsonb"),
    )
    planning_notes: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    planner_summary: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )


class KnowledgeItemModel(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "knowledge_items"
    __table_args__ = (
        sa.Index("ix_knowledge_items_source_type_deleted_at", "source_type", "deleted_at"),
        sa.Index(
            "ix_knowledge_items_retrieval_metadata_gin",
            "retrieval_metadata",
            postgresql_using="gin",
        ),
    )

    knowledge_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), primary_key=True)
    title: Mapped[str] = mapped_column(sa.String(NAME_LENGTH), nullable=False)
    source_type: Mapped[str] = mapped_column(sa.String(SHORT_CODE_LENGTH), nullable=False)
    summary: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    version: Mapped[str | None] = mapped_column(sa.String(NAME_LENGTH), nullable=True)
    body_text: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    retrieval_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
    )
    primary_artifact_id: Mapped[str | None] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("artifact_references.artifact_id", ondelete="SET NULL"),
        nullable=True,
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(DEFAULT_VECTOR_DIMENSIONS), nullable=True)


class TeachingSampleModel(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "teaching_samples"
    __table_args__ = (
        sa.Index(
            "ix_teaching_samples_task_type_target_object_workstation_id",
            "task_type",
            "target_object",
            "workstation_id",
        ),
        sa.Index(
            "ix_teaching_samples_retrieval_metadata_gin",
            "retrieval_metadata",
            postgresql_using="gin",
        ),
    )

    sample_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), primary_key=True)
    title: Mapped[str] = mapped_column(sa.String(NAME_LENGTH), nullable=False)
    summary: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    task_type: Mapped[TaskType | None] = mapped_column(
        sql_enum(TaskType, "task_type_enum"),
        nullable=True,
    )
    target_object: Mapped[str | None] = mapped_column(sa.String(NAME_LENGTH), nullable=True)
    workstation_id: Mapped[str | None] = mapped_column(sa.String(STRING_ID_LENGTH), nullable=True)
    robot_id: Mapped[str | None] = mapped_column(sa.String(STRING_ID_LENGTH), nullable=True)
    success_rate: Mapped[Decimal | None] = mapped_column(sa.Numeric(5, 4), nullable=True)
    sample_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
    )
    retrieval_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
    )
    primary_artifact_id: Mapped[str | None] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("artifact_references.artifact_id", ondelete="SET NULL"),
        nullable=True,
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(DEFAULT_VECTOR_DIMENSIONS), nullable=True)


class ExecutionPlanModel(Base):
    __tablename__ = "execution_plans"
    __table_args__ = (
        sa.Index("ix_execution_plans_task_id_generated_at", "task_id", "generated_at"),
        sa.Index("ix_execution_plans_allowed_to_run_generated_at", "allowed_to_run", "generated_at"),
    )

    plan_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), primary_key=True)
    task_id: Mapped[str] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("tasks.task_id", ondelete="CASCADE"),
        nullable=False,
    )
    semantic_plan_id: Mapped[str] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("semantic_action_plans.semantic_plan_id", ondelete="CASCADE"),
        nullable=False,
    )
    steps: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    action_params: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=sa.text("'[]'::jsonb"),
    )
    preconditions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=sa.text("'[]'::jsonb"),
    )
    validation_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    allowed_to_run: Mapped[bool] = mapped_column(
        sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
    )
    script_version: Mapped[str | None] = mapped_column(sa.String(NAME_LENGTH), nullable=True)
    script_artifact_id: Mapped[str | None] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("artifact_references.artifact_id", ondelete="SET NULL"),
        nullable=True,
    )
    generated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    last_validated_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)


class ExecutionResultModel(Base):
    __tablename__ = "execution_results"
    __table_args__ = (
        sa.Index("ix_execution_results_task_id_finished_at", "task_id", "finished_at"),
        sa.Index("ix_execution_results_robot_status_finished_at", "robot_status", "finished_at"),
    )

    execution_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), primary_key=True)
    task_id: Mapped[str] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("tasks.task_id", ondelete="CASCADE"),
        nullable=False,
    )
    plan_id: Mapped[str | None] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("execution_plans.plan_id", ondelete="SET NULL"),
        nullable=True,
    )
    robot_status: Mapped[RobotExecutionStatus] = mapped_column(
        sql_enum(RobotExecutionStatus, "robot_execution_status_enum"),
        nullable=False,
    )
    error_code: Mapped[str | None] = mapped_column(sa.String(NAME_LENGTH), nullable=True)
    vision_verification: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    memory_written: Mapped[bool] = mapped_column(
        sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
    )
    started_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(sa.Text(), nullable=True)
    primary_artifact_id: Mapped[str | None] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("artifact_references.artifact_id", ondelete="SET NULL"),
        nullable=True,
    )


class AlertModel(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        sa.Index("ix_alerts_task_id_occurred_at", "task_id", "occurred_at"),
        sa.Index("ix_alerts_handling_status_occurred_at", "handling_status", "occurred_at"),
        sa.Index("ix_alerts_severity_occurred_at", "severity", "occurred_at"),
        sa.Index("ix_alerts_related_audit_event_id", "related_audit_event_id"),
    )

    alert_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), primary_key=True)
    task_id: Mapped[str | None] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("tasks.task_id", ondelete="SET NULL"),
        nullable=True,
    )
    related_audit_event_id: Mapped[str | None] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("audit_records.audit_event_id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[AlertEventType] = mapped_column(
        sql_enum(AlertEventType, "alert_event_type_enum"),
        nullable=False,
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        sql_enum(AlertSeverity, "alert_severity_enum"),
        nullable=False,
    )
    trigger_module: Mapped[ModuleName] = mapped_column(
        sql_enum(ModuleName, "module_name_enum"),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    handling_status: Mapped[AlertHandlingStatus] = mapped_column(
        sql_enum(AlertHandlingStatus, "alert_handling_status_enum"),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    emergency_stop_triggered: Mapped[bool] = mapped_column(
        sa.Boolean(),
        nullable=False,
        server_default=sa.false(),
    )


class AuditRecordModel(Base):
    __tablename__ = "audit_records"
    __table_args__ = (
        sa.Index("ix_audit_records_task_id_occurred_at", "task_id", "occurred_at"),
        sa.Index("ix_audit_records_source_module_occurred_at", "source_module", "occurred_at"),
        sa.Index("ix_audit_records_status_to_occurred_at", "status_to", "occurred_at"),
    )

    audit_event_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), primary_key=True)
    task_id: Mapped[str | None] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("tasks.task_id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[AuditEventType] = mapped_column(
        sql_enum(AuditEventType, "audit_event_type_enum"),
        nullable=False,
    )
    source_module: Mapped[ModuleName] = mapped_column(
        sql_enum(ModuleName, "module_name_enum"),
        nullable=False,
    )
    outcome: Mapped[AuditOutcome] = mapped_column(
        sql_enum(AuditOutcome, "audit_outcome_enum"),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    summary: Mapped[str] = mapped_column(sa.Text(), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(sa.String(NAME_LENGTH), nullable=True)
    status_from: Mapped[TaskStatus | None] = mapped_column(
        sql_enum(TaskStatus, "task_status_enum"),
        nullable=True,
    )
    status_to: Mapped[TaskStatus | None] = mapped_column(
        sql_enum(TaskStatus, "task_status_enum"),
        nullable=True,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
    )


class LongTermMemoryModel(Base):
    __tablename__ = "long_term_memories"
    __table_args__ = (
        sa.Index(
            "ix_long_term_memories_workstation_id_task_type_target_object",
            "workstation_id",
            "task_type",
            "target_object",
        ),
        sa.Index(
            "ix_long_term_memories_robot_id_recorded_at",
            "robot_id",
            "recorded_at",
        ),
        sa.Index(
            "ix_long_term_memories_retrieval_metadata_gin",
            "retrieval_metadata",
            postgresql_using="gin",
        ),
    )

    memory_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), primary_key=True)
    task_id: Mapped[str] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("tasks.task_id", ondelete="CASCADE"),
        nullable=False,
    )
    task_type: Mapped[TaskType] = mapped_column(sql_enum(TaskType, "task_type_enum"), nullable=False)
    target_object: Mapped[str] = mapped_column(sa.String(NAME_LENGTH), nullable=False)
    workstation_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), nullable=False)
    robot_id: Mapped[str] = mapped_column(sa.String(STRING_ID_LENGTH), nullable=False)
    robot_config_id: Mapped[str | None] = mapped_column(
        sa.String(STRING_ID_LENGTH),
        sa.ForeignKey("robot_configs.robot_config_id", ondelete="SET NULL"),
        nullable=True,
    )
    scene_label: Mapped[str | None] = mapped_column(sa.String(NAME_LENGTH), nullable=True)
    key_grasp_parameters: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
    )
    placement_parameters: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
    )
    retrieval_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
    )
    script_version: Mapped[str] = mapped_column(sa.String(NAME_LENGTH), nullable=False)
    vision_verification: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(DEFAULT_VECTOR_DIMENSIONS), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    source_label: Mapped[str] = mapped_column(sa.String(SHORT_CODE_LENGTH), nullable=False)
