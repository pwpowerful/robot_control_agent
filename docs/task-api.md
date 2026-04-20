# Task API

This document records the Step 11 task API behavior currently implemented in the repository.

## Endpoints

```text
POST /api/tasks
GET  /api/tasks
GET  /api/tasks/{task_id}
GET  /api/tasks/{task_id}/execution-chain
GET  /api/tasks/_access-check
```

## Permissions

- `POST /api/tasks`: requires `task:create`
- `GET /api/tasks`: requires `task:read`
- `GET /api/tasks/{task_id}`: requires `task_detail:read`
- `GET /api/tasks/{task_id}/execution-chain`: requires `execution:view`

## Create Payload

Task creation currently requires:

- `raw_instruction`
- `target_object`
- `workstation_id`
- `target_location.station_id`
- `target_location.pose.frame_id`
- `target_location.pose`
- `target_location.tolerance_mm > 0`

The current Step 11 API also requires `workstation_id` to match `target_location.station_id`, because the MVP is still locked to a single workstation context.

## Execution Prerequisites

Even when the payload shape is valid, task creation is rejected unless the following minimum execution prerequisites are satisfied:

- `RCA_EXECUTION_ROBOT_CONFIG_ID` is configured
- `RCA_SAFETY_RULE_SET_ID` is configured
- `RCA_SAFETY_EMERGENCY_STOP_ENABLED=true`

When these checks fail, the API returns:

- HTTP status `422`
- error code `task.prerequisite_failed`
- a structured `details` array describing each blocking prerequisite

## Detail Contract

The current task detail endpoint returns the Step 11 minimum field set directly from `TaskRecord`, including:

- task id
- raw instruction
- target object
- target location
- status
- failure reason
- creator
- creation time
- robot id
- workstation id

## Execution Chain Contract

The execution-chain endpoint currently returns:

- the current `TaskRecord`
- `status_history`
- `audit_chain`
- `semantic_action_plan`
- `execution_plan`
- `execution_result`

At Step 11, the plan and execution objects are placeholders and remain `null` until later execution steps are implemented.

## Current Storage Model

Step 11 intentionally stores task aggregates in-process inside `backend/src/robot_control_backend/task_service/`.

This current implementation already settles:

- the API contract
- input completeness validation
- minimum execution prerequisite validation
- task id generation
- initial `created` status recording
- task status history recording
- task-scoped audit chain creation

Database persistence for tasks, plans, execution results, and status history will be introduced in later steps.
