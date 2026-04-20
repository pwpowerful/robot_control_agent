# API Conventions

This document records the Step 10 and Step 11 backend API contract currently implemented in the repository.

## Scope

The current API surface now includes the framework baseline plus the first task business endpoints. It exposes:

- authentication and session bootstrap
- task creation, task list, task detail, and task execution-chain queries
- protected access-check endpoints for the remaining planned business groups
- system health and version endpoints
- OpenAPI docs and a unified error-handling contract

Alert CRUD, audit queries, knowledge CRUD, and configuration CRUD will be added in later steps. Task persistence still remains in-process for Step 11.

## API Groups

The current OpenAPI groups are:

- `auth`
- `tasks`
- `plans`
- `alerts`
- `audit`
- `knowledge`
- `config`
- `system`

## Response Envelope

Successful responses use:

```json
{
  "success": true,
  "data": {},
  "meta": {
    "request_id": "req-123",
    "api_version": "v1",
    "timestamp": "2026-04-20T12:00:00Z",
    "pagination": null
  }
}
```

Error responses use:

```json
{
  "success": false,
  "error": {
    "code": "auth.permission_denied",
    "message": "Missing permission: audit:read",
    "details": {
      "required_permission": "audit:read"
    }
  },
  "meta": {
    "request_id": "req-123",
    "api_version": "v1",
    "timestamp": "2026-04-20T12:00:00Z",
    "pagination": null
  }
}
```

## Response Metadata

- `request_id`: per-request identifier. The server echoes the incoming `X-Request-ID` header when present, otherwise it generates one.
- `api_version`: current API contract version. Step 10 and Step 11 keep this fixed as `v1`.
- `timestamp`: server-side UTC timestamp when the envelope is created.
- `pagination`: populated for list endpoints such as `GET /api/tasks`, and `null` for non-list responses.

## Response Headers

Every API response currently returns:

- `X-Request-ID`
- `X-API-Version`

## Error Codes

The current structured error code set is:

- `auth.authentication_required`: no valid session cookie was resolved.
- `auth.invalid_credentials`: login credentials were rejected.
- `auth.permission_denied`: the current session lacks the required RBAC permission.
- `request.validation_error`: FastAPI request validation failed.
- `resource.not_found`: no matching route or resource exists.
- `task.not_found`: the requested task id does not exist.
- `task.prerequisite_failed`: the request shape is valid, but minimum task execution prerequisites are not satisfied.
- `request.http_error`: fallback code for framework HTTP errors without a more specific mapping.
- `system.not_implemented`: reserved for future explicit `501` endpoints.
- `system.internal_error`: unexpected server-side exception.

## Current Endpoints

```text
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

## Step 11 Task Endpoint Rules

- `POST /api/tasks`
  - requires `task:create`
  - validates non-empty instruction, target object, workstation, and target location fields
  - validates that `workstation_id` matches `target_location.station_id`
  - validates that `RCA_EXECUTION_ROBOT_CONFIG_ID` and `RCA_SAFETY_RULE_SET_ID` are configured
  - validates that `RCA_SAFETY_EMERGENCY_STOP_ENABLED=true`
  - returns a `TaskRecord` inside the shared success envelope
- `GET /api/tasks`
  - requires `task:read`
  - returns paginated task summaries via `meta.pagination`
- `GET /api/tasks/{task_id}`
  - requires `task_detail:read`
  - returns the task detail fields required by the task detail page
- `GET /api/tasks/{task_id}/execution-chain`
  - requires `execution:view`
  - returns task summary, status history, audit chain, and current plan/execution placeholders

OpenAPI and docs endpoints remain:

- `/openapi.json`
- `/docs`
- `/redoc`
