from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable


class RoleCode(StrEnum):
    """Supported human roles for the current MVP."""

    OPERATOR = "operator"
    ADMIN = "admin"


class PermissionCode(StrEnum):
    """RBAC permission set covering the Step 09 boundary."""

    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_DETAIL_READ = "task_detail:read"
    EXECUTION_VIEW = "execution:view"
    ALERT_READ = "alert:read"
    ALERT_HANDLE = "alert:handle"
    ROBOT_CONFIG_MANAGE = "robot_config:manage"
    SAFETY_RULES_MANAGE = "safety_rules:manage"
    KNOWLEDGE_ITEMS_MANAGE = "knowledge_items:manage"
    TEACHING_SAMPLES_MANAGE = "teaching_samples:manage"
    AUDIT_READ = "audit:read"


class PageCode(StrEnum):
    """Web-console page areas used to express role-based page access."""

    TASKS = "tasks"
    TASK_DETAILS = "task_details"
    ALERTS = "alerts"
    ROBOT_CONFIG = "config_robot"
    SAFETY_RULES = "config_safety_rules"
    KNOWLEDGE_ITEMS = "knowledge_items"
    KNOWLEDGE_SAMPLES = "knowledge_samples"
    AUDIT = "audit"


@dataclass(frozen=True)
class RoleDefinition:
    """Complete role definition used by the auth service and docs."""

    role_code: RoleCode
    display_name: str
    description: str
    permissions: frozenset[PermissionCode]
    page_access: frozenset[PageCode]
    interface_groups: tuple[str, ...]
    data_access_scope: tuple[str, ...]
    audit_access_scope: str


OPERATOR_DEFINITION = RoleDefinition(
    role_code=RoleCode.OPERATOR,
    display_name="操作员",
    description="创建任务，查看任务详情、执行结果与告警，但不修改系统配置。",
    permissions=frozenset(
        {
            PermissionCode.TASK_CREATE,
            PermissionCode.TASK_READ,
            PermissionCode.TASK_DETAIL_READ,
            PermissionCode.EXECUTION_VIEW,
            PermissionCode.ALERT_READ,
        }
    ),
    page_access=frozenset(
        {
            PageCode.TASKS,
            PageCode.TASK_DETAILS,
            PageCode.ALERTS,
        }
    ),
    interface_groups=("tasks", "alerts"),
    data_access_scope=(
        "create_task",
        "view_task_status",
        "view_execution_plan",
        "view_execution_result",
        "view_alerts",
    ),
    audit_access_scope="none",
)

ADMIN_DEFINITION = RoleDefinition(
    role_code=RoleCode.ADMIN,
    display_name="管理员",
    description="包含操作员能力，并负责机器人配置、安全规则、知识库、示教样本、告警处理和审计查看。",
    permissions=frozenset(
        set(OPERATOR_DEFINITION.permissions)
        | {
            PermissionCode.ALERT_HANDLE,
            PermissionCode.ROBOT_CONFIG_MANAGE,
            PermissionCode.SAFETY_RULES_MANAGE,
            PermissionCode.KNOWLEDGE_ITEMS_MANAGE,
            PermissionCode.TEACHING_SAMPLES_MANAGE,
            PermissionCode.AUDIT_READ,
        }
    ),
    page_access=frozenset(
        set(OPERATOR_DEFINITION.page_access)
        | {
            PageCode.ROBOT_CONFIG,
            PageCode.SAFETY_RULES,
            PageCode.KNOWLEDGE_ITEMS,
            PageCode.KNOWLEDGE_SAMPLES,
            PageCode.AUDIT,
        }
    ),
    interface_groups=(
        "tasks",
        "alerts",
        "config.robot",
        "config.safety_rules",
        "knowledge.items",
        "knowledge.samples",
        "audit",
    ),
    data_access_scope=(
        "create_task",
        "view_task_status",
        "view_execution_plan",
        "view_execution_result",
        "view_alerts",
        "handle_alerts",
        "manage_robot_configs",
        "manage_safety_rule_sets",
        "manage_knowledge_items",
        "manage_teaching_samples",
        "view_audit_logs",
    ),
    audit_access_scope="full",
)


ROLE_DEFINITIONS: dict[RoleCode, RoleDefinition] = {
    RoleCode.OPERATOR: OPERATOR_DEFINITION,
    RoleCode.ADMIN: ADMIN_DEFINITION,
}


def get_role_definition(role_code: RoleCode) -> RoleDefinition:
    """Return the canonical definition for a role code."""
    return ROLE_DEFINITIONS[role_code]


def permissions_for_roles(role_codes: Iterable[RoleCode]) -> frozenset[PermissionCode]:
    """Expand one or more role codes into the effective permission set."""
    permissions: set[PermissionCode] = set()
    for role_code in role_codes:
        permissions.update(get_role_definition(role_code).permissions)
    return frozenset(permissions)


def pages_for_roles(role_codes: Iterable[RoleCode]) -> frozenset[PageCode]:
    """Expand one or more role codes into the effective page access set."""
    pages: set[PageCode] = set()
    for role_code in role_codes:
        pages.update(get_role_definition(role_code).page_access)
    return frozenset(pages)
