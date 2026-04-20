from __future__ import annotations

from pathlib import Path

from robot_control_backend.database import (
    DEFAULT_VECTOR_DIMENSIONS,
    Base,
    Vector,
)


def test_database_metadata_covers_step_06_core_tables() -> None:
    expected_tables = {
        "users",
        "roles",
        "user_roles",
        "sessions",
        "artifact_references",
        "robot_configs",
        "safety_rule_sets",
        "system_configs",
        "tasks",
        "semantic_action_plans",
        "execution_plans",
        "execution_results",
        "alerts",
        "audit_records",
        "knowledge_items",
        "teaching_samples",
        "long_term_memories",
    }

    assert expected_tables <= set(Base.metadata.tables)


def test_database_metadata_defines_expected_constraints_and_indexes() -> None:
    users_table = Base.metadata.tables["users"]
    system_configs_table = Base.metadata.tables["system_configs"]
    execution_plans_table = Base.metadata.tables["execution_plans"]
    tasks_table = Base.metadata.tables["tasks"]
    alerts_table = Base.metadata.tables["alerts"]
    audit_records_table = Base.metadata.tables["audit_records"]
    knowledge_items_table = Base.metadata.tables["knowledge_items"]

    user_unique_names = {
        constraint.name
        for constraint in users_table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    system_config_unique_names = {
        constraint.name
        for constraint in system_configs_table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    execution_plan_fk_targets = {
        foreign_key.target_fullname for foreign_key in execution_plans_table.foreign_keys
    }
    alerts_fk_targets = {foreign_key.target_fullname for foreign_key in alerts_table.foreign_keys}

    assert "uq_users_username" in user_unique_names
    assert "uq_system_configs_config_namespace_config_key" in system_config_unique_names
    assert execution_plan_fk_targets == {
        "artifact_references.artifact_id",
        "semantic_action_plans.semantic_plan_id",
        "tasks.task_id",
    }
    assert alerts_fk_targets == {
        "audit_records.audit_event_id",
        "tasks.task_id",
    }

    assert {index.name for index in tasks_table.indexes} >= {
        "ix_tasks_status_created_at",
        "ix_tasks_robot_id_created_at",
        "ix_tasks_workstation_id_created_at",
    }
    assert {index.name for index in alerts_table.indexes} >= {
        "ix_alerts_handling_status_occurred_at",
        "ix_alerts_related_audit_event_id",
        "ix_alerts_severity_occurred_at",
    }
    assert {index.name for index in audit_records_table.indexes} >= {
        "ix_audit_records_task_id_occurred_at",
        "ix_audit_records_status_to_occurred_at",
    }
    assert {index.name for index in knowledge_items_table.indexes} >= {
        "ix_knowledge_items_source_type_deleted_at",
        "ix_knowledge_items_retrieval_metadata_gin",
    }


def test_vector_backed_tables_reserve_embedding_columns() -> None:
    for table_name in ("knowledge_items", "teaching_samples", "long_term_memories"):
        embedding_column = Base.metadata.tables[table_name].columns["embedding"]

        assert isinstance(embedding_column.type, Vector)
        assert embedding_column.type.dimensions == DEFAULT_VECTOR_DIMENSIONS


def test_initial_migration_declares_pgvector_extension_and_hnsw_indexes() -> None:
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "20260416_01_initial_schema.py"
    )
    migration_text = migration_path.read_text(encoding="utf-8")

    assert 'revision = "20260416_01"' in migration_text
    assert "CREATE EXTENSION IF NOT EXISTS vector" in migration_text
    assert "ix_knowledge_items_embedding_hnsw" in migration_text
    assert "ix_teaching_samples_embedding_hnsw" in migration_text
    assert "ix_long_term_memories_embedding_hnsw" in migration_text


def test_step_07_migration_adds_alert_audit_link_and_audit_event_types() -> None:
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "20260420_01_step07_audit_alert_models.py"
    )
    migration_text = migration_path.read_text(encoding="utf-8")

    assert 'revision = "20260420_01"' in migration_text
    assert "ALTER TYPE audit_event_type_enum ADD VALUE IF NOT EXISTS" in migration_text
    assert '"context_assembled"' in migration_text
    assert '"tool_called"' in migration_text
    assert '"agent_output_recorded"' in migration_text
    assert 'sa.Column("related_audit_event_id", sa.String(length=128), nullable=True)' in migration_text
    assert '"fk_alerts_related_audit_event_id_audit_records"' in migration_text
    assert '"ix_alerts_related_audit_event_id"' in migration_text
