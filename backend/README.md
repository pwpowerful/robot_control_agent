# Backend Directory

This directory contains the backend foundation for the robotic arm control agent MVP.

## Current Scope

Steps 03 through 11 currently establish the backend baseline, schema foundation, configuration guardrails, RBAC auth shell, unified API framework, and the first real task APIs:

- Python 3.11 project managed by `uv`
- dependency and lockfile conventions
- minimal FastAPI startup entry
- centralized configuration loading
- structured logging bootstrap
- environment isolation rules for development, test, and production
- shared domain contracts and task state machine
- SQLAlchemy ORM metadata for the Step 06 core schema
- audit and alert policy definitions for Step 07
- Alembic migration scaffold plus Step 06 and Step 07 PostgreSQL revisions
- unified Step 08 configuration management for database, model provider, vision, robot, auth, audit, safety, and artifact storage
- conservative defaults that keep the system in simulated mode unless real execution is explicitly unlocked
- Step 09 bootstrap authentication using server-side sessions, HTTP-only cookies, and operator/admin RBAC boundaries
- Step 10 grouped API routers, shared success/error envelopes, request-id propagation, and system health/version endpoints
- Step 11 task creation, list, detail, and execution-chain query APIs backed by an in-process task service

Database-backed services, repositories, and runtime execution flows will be implemented in later steps. Step 11 currently keeps task data in-process so the API contract, validation rules, status history, and audit chain can settle before persistence is introduced.

## Directory Layout

- `pyproject.toml`: project metadata, dependencies, scripts, and test settings
- `uv.lock`: committed lockfile for reproducible installs
- `.python-version`: pinned Python major/minor version for local development
- `.env.example`: shared configuration example
- `.env.development.example`: development override example
- `.env.test.example`: test override example
- `.env.production.example`: production override example
- `alembic.ini`: Alembic configuration entry
- `alembic/`: migration environment and revision history
- `src/robot_control_backend/`: backend application package
- `tests/`: startup, configuration, domain, state-machine, and schema baseline tests

## Dependency Management Convention

- Package manager: `uv`
- Python version: `3.11`
- Install command: `uv sync`
- Lockfile strategy: commit `uv.lock` to keep dependency resolution consistent across machines
- Runtime dependencies are declared in `[project.dependencies]`
- Development-only dependencies are declared in `[dependency-groups.dev]`

## Configuration Convention

- All backend environment variables use the `RCA_` prefix
- Load order is:
  1. process environment variables
  2. `.env.<environment>`
  3. `.env`
  4. code defaults
- `RCA_APP_ENV` controls environment isolation and supports:
  - `development`
  - `test`
  - `production`
- Unified configuration groups currently include:
  - app and logging
  - database
  - shared model provider
  - vision adapter
  - robot adapter
  - auth/session defaults
  - audit retention
  - safety defaults
  - artifact storage
- Database migrations require `RCA_DATABASE_URL` from either the process environment, `.env.<environment>`, or `.env`
- Production currently requires:
  - `RCA_DATABASE_URL`
  - `RCA_SHARED_MODEL_API_KEY`
- Real execution is blocked unless the configuration explicitly provides:
  - `RCA_EXECUTION_ALLOW_REAL_HARDWARE=true`
  - `RCA_EXECUTION_ROBOT_CONFIG_ID`
  - `RCA_SAFETY_RULE_SET_ID`
  - `RCA_DATABASE_URL`
  - `RCA_SHARED_MODEL_API_KEY`
  - `RCA_SAFETY_EMERGENCY_STOP_ENABLED=true`
- Additional real-adapter requirements:
  - `RCA_ROBOT_CONTROL_ENDPOINT` when `RCA_ROBOT_ADAPTER_MODE=real`
  - `RCA_VISION_CALIBRATION_FILE` when `RCA_VISION_ADAPTER_MODE=real`
- Conservative defaults keep both adapters in `simulated` mode, leave real-hardware execution disabled, enable emergency stop, and cap task/model timeouts
- `RCA_AUDIT_STORE_RAW_REASONING` must remain `false`
- Artifact storage defaults to a writable local path, but shared environments should set `RCA_ARTIFACT_ROOT_DIR` explicitly
- Current Step 09 auth flow also requires bootstrap credentials from config:
  - `RCA_AUTH_ADMIN_USERNAME`
  - `RCA_AUTH_ADMIN_PASSWORD`
  - `RCA_AUTH_OPERATOR_USERNAME`
  - `RCA_AUTH_OPERATOR_PASSWORD`
- Production must override the default bootstrap passwords for both roles

## Startup Convention

- Validate configuration:

```powershell
uv run robot-control-config-check
```

- `robot-control-config-check` prints a safe summary and runs optional preflight checks
- Enable database reachability preflight with `RCA_DATABASE_CONNECTIVITY_CHECK=true`

- Start the API server:

```powershell
uv run robot-control-api
```

The current minimal runnable state is a FastAPI application with OpenAPI docs, system endpoints, auth endpoints, protected access-contract routes, and Step 11 task business APIs.

## Database Baseline

- Database stack: `PostgreSQL 16 + SQLAlchemy 2.0 + Psycopg 3 + Alembic`
- Vector search baseline: `pgvector` via the PostgreSQL `vector` extension
- ORM package: `src/robot_control_backend/database/`
- Initial revision: `20260416_01`
- Current head revision: `20260420_01`
- Step 06 and Step 07 scope stops at metadata, constraints, indexes, migration files, audit/alert rules, and docs
- The backend still does not yet add database sessions, repositories, service-layer persistence, or task queue logic

Core schema groups currently covered:

- Authentication and RBAC: `users`, `roles`, `user_roles`, `sessions`
- Task execution trace: `tasks`, `semantic_action_plans`, `execution_plans`, `execution_results`
- Audit and alerts: `alerts`, `audit_records`
- Knowledge and memory: `knowledge_items`, `teaching_samples`, `long_term_memories`
- Config and artifacts: `artifact_references`, `robot_configs`, `safety_rule_sets`, `system_configs`

Migration commands:

```powershell
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head --sql
```

## Logging Convention

- Default format: structured JSON to stdout
- Optional local format: set `RCA_LOG_FORMAT=console`
- Log level is controlled by `RCA_LOG_LEVEL`
- Startup and shutdown events are logged by the API app lifecycle

## Step 08 Defaults

- Model provider credentials are isolated behind `RCA_SHARED_MODEL_API_KEY` and are never echoed by the config-check command
- Safety defaults ship with conservative forbidden zones, joint limits, a `60` second task timeout, and emergency stop enabled
- Shared model calls default to a `20` second timeout with `1` retry
- Vision and robot adapters default to simulated backends
- Artifact directories are validated on startup and auto-created when `RCA_ARTIFACT_AUTO_CREATE=true`

## Step 09 Auth Shell

- Auth strategy: server-side session + HTTP-only cookie + RBAC
- Current implementation uses two bootstrap users from environment variables:
  - operator
  - admin
- Session cookies use the configured `RCA_AUTH_SESSION_COOKIE_NAME`, `RCA_AUTH_SESSION_TTL_MINUTES`, `RCA_AUTH_REQUIRE_SECURE_COOKIES`, and `RCA_AUTH_COOKIE_SAME_SITE`
- The current auth service is intentionally small and in-process so Step 09 can lock permission boundaries before later database-backed user/session persistence is added
- Role boundaries currently enforced by protected API groups:
  - operator: task access, task detail access, execution/alert viewing
  - admin: operator access plus robot config, safety rules, knowledge items, teaching samples, alert handling, and audit access

## Step 10 / Step 11 API Contract

- OpenAPI groups currently exposed:
  - `auth`
  - `tasks`
  - `plans`
  - `alerts`
  - `audit`
  - `knowledge`
  - `config`
  - `system`
- All JSON responses now follow one of two envelopes:
  - success: `success + data + meta`
  - error: `success + error + meta`
- Shared metadata fields currently include:
  - `request_id`
  - `api_version`
  - `timestamp`
  - `pagination` for future list endpoints
- Shared API response headers:
  - `X-Request-ID`
  - `X-API-Version`
- Current structured error codes include:
  - `auth.authentication_required`
  - `auth.invalid_credentials`
  - `auth.permission_denied`
  - `request.validation_error`
  - `resource.not_found`
  - `task.not_found`
  - `task.prerequisite_failed`
  - `request.http_error`
  - `system.not_implemented`
  - `system.internal_error`
- Full contract details live in `../docs/api-conventions.md`

Current framework and Step 11 task endpoints:

```powershell
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
GET  /api/auth/permission-matrix
POST /api/tasks
GET  /api/tasks
GET  /api/tasks/{task_id}
GET  /api/tasks/{task_id}/execution-chain
GET  /api/tasks/_access-check
GET  /api/plans/_access-check
GET  /api/alerts/_access-check
POST /api/alerts/_handle-check
POST /api/config/robot/_access-check
POST /api/config/safety-rules/_access-check
POST /api/knowledge/items/_access-check
POST /api/knowledge/samples/_access-check
GET  /api/audit/_access-check
GET  /api/system/health
GET  /api/system/version
```

## Step 11 Task API Notes

- Task creation requires:
  - `TASK_CREATE` permission
  - a valid task payload with non-empty instruction, target object, workstation, and target location
  - `RCA_EXECUTION_ROBOT_CONFIG_ID`
  - `RCA_SAFETY_RULE_SET_ID`
  - `RCA_SAFETY_EMERGENCY_STOP_ENABLED=true`
- Task list requires `TASK_READ`
- Task detail requires `TASK_DETAIL_READ`
- Task execution-chain query requires `EXECUTION_VIEW`
- The current Step 11 task backend is `src/robot_control_backend/task_service/`
- Task creation currently records:
  - a unique task id
  - initial `created` status
  - task status history
  - task-scoped audit chain entries for `task_created` and `task_status_changed`
- The current task list endpoint already uses the shared `pagination` metadata field

## First-Time Setup

```powershell
Copy-Item .env.example .env
Copy-Item .env.development.example .env.development
uv sync --group dev
uv run robot-control-config-check
uv run robot-control-api
```

To prepare local database migrations, also set `RCA_DATABASE_URL` in `.env` or `.env.development` and then run:

```powershell
uv run alembic upgrade head
```
