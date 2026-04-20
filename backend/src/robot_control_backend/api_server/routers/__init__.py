"""Grouped API routers for the current backend foundation."""

from robot_control_backend.api_server.routers.alerts import router as alerts_router
from robot_control_backend.api_server.routers.audit import router as audit_router
from robot_control_backend.api_server.routers.auth import router as auth_router
from robot_control_backend.api_server.routers.config import router as config_router
from robot_control_backend.api_server.routers.knowledge import router as knowledge_router
from robot_control_backend.api_server.routers.plans import router as plans_router
from robot_control_backend.api_server.routers.system import router as system_router
from robot_control_backend.api_server.routers.tasks import router as tasks_router

OPENAPI_TAGS = [
    {
        "name": "auth",
        "description": "Authentication, session bootstrap, and RBAC matrix endpoints.",
    },
    {
        "name": "tasks",
        "description": "Task-related API group covering Step 11 task creation, list, detail, and execution-chain queries.",
    },
    {
        "name": "plans",
        "description": "Execution plan and script summary API group. Step 10 currently exposes access-contract endpoints.",
    },
    {
        "name": "alerts",
        "description": "Alert query and handling API group. Step 10 currently exposes access-contract endpoints.",
    },
    {
        "name": "audit",
        "description": "Audit query API group. Step 10 currently exposes access-contract endpoints.",
    },
    {
        "name": "knowledge",
        "description": "Knowledge item and teaching sample API group. Step 10 currently exposes access-contract endpoints.",
    },
    {
        "name": "config",
        "description": "System configuration API group covering robot and safety-rule configuration.",
    },
    {
        "name": "system",
        "description": "System health, version, and service-metadata endpoints.",
    },
]

API_ROUTERS = (
    auth_router,
    tasks_router,
    plans_router,
    alerts_router,
    audit_router,
    knowledge_router,
    config_router,
    system_router,
)

__all__ = [
    "API_ROUTERS",
    "OPENAPI_TAGS",
    "alerts_router",
    "audit_router",
    "auth_router",
    "config_router",
    "knowledge_router",
    "plans_router",
    "system_router",
    "tasks_router",
]
