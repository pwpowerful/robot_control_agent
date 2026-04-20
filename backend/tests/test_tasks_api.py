from __future__ import annotations

from fastapi.testclient import TestClient

from robot_control_backend.api_server.app import create_app


def _build_client(
    monkeypatch,
    *,
    execution_robot_config_id: str | None = "robot-sim-01",
    safety_rule_set_id: str | None = "safety-default",
    safety_emergency_stop_enabled: bool = True,
) -> TestClient:
    monkeypatch.setenv("RCA_APP_ENV", "test")
    monkeypatch.setenv("RCA_LOG_FORMAT", "console")
    monkeypatch.setenv("RCA_AUTH_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("RCA_AUTH_ADMIN_PASSWORD", "admin-secret")
    monkeypatch.setenv("RCA_AUTH_OPERATOR_USERNAME", "operator")
    monkeypatch.setenv("RCA_AUTH_OPERATOR_PASSWORD", "operator-secret")

    if execution_robot_config_id is None:
        monkeypatch.delenv("RCA_EXECUTION_ROBOT_CONFIG_ID", raising=False)
    else:
        monkeypatch.setenv("RCA_EXECUTION_ROBOT_CONFIG_ID", execution_robot_config_id)

    if safety_rule_set_id is None:
        monkeypatch.delenv("RCA_SAFETY_RULE_SET_ID", raising=False)
    else:
        monkeypatch.setenv("RCA_SAFETY_RULE_SET_ID", safety_rule_set_id)

    monkeypatch.setenv(
        "RCA_SAFETY_EMERGENCY_STOP_ENABLED",
        "true" if safety_emergency_stop_enabled else "false",
    )
    return TestClient(create_app())


def _login(client: TestClient, username: str, password: str):
    return client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )


def _unwrap_success(response):
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["meta"]["api_version"] == "v1"
    assert body["meta"]["request_id"]
    assert body["meta"]["timestamp"]
    return body["data"]


def _unwrap_error(response, *, status_code: int, code: str, message: str | None = None):
    assert response.status_code == status_code
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == code
    if message is not None:
        assert body["error"]["message"] == message
    assert body["meta"]["api_version"] == "v1"
    assert body["meta"]["request_id"]
    return body


def _task_payload() -> dict[str, object]:
    return {
        "raw_instruction": "把红色方块放到 station-a 的 slot-1。",
        "target_object": "red_block",
        "workstation_id": "station-a",
        "target_location": {
            "station_id": "station-a",
            "slot_id": "slot-1",
            "pose": {
                "frame_id": "workspace",
                "x_mm": 120.5,
                "y_mm": 45.0,
                "z_mm": 18.0,
                "rx_deg": 0.0,
                "ry_deg": 0.0,
                "rz_deg": 90.0,
            },
            "tolerance_mm": 5.0,
        },
    }


def test_operator_can_create_list_detail_and_query_execution_chain(monkeypatch) -> None:
    with _build_client(monkeypatch) as client:
        _unwrap_success(_login(client, "operator", "operator-secret"))

        create_response = client.post(
            "/api/tasks",
            json=_task_payload(),
            headers={"X-Request-ID": "req-task-create-001"},
        )
        created_task = _unwrap_success(create_response)

        list_response = client.get("/api/tasks", params={"page": 1, "page_size": 10})
        detail_response = client.get(f"/api/tasks/{created_task['task_id']}")
        chain_response = client.get(f"/api/tasks/{created_task['task_id']}/execution-chain")

    assert create_response.headers["X-Request-ID"] == "req-task-create-001"
    assert create_response.headers["X-API-Version"] == "v1"
    assert created_task["task_id"].startswith("task-")
    assert created_task["status"] == "created"
    assert created_task["raw_instruction"] == _task_payload()["raw_instruction"]
    assert created_task["target_object"] == "red_block"
    assert created_task["failure_reason"] is None
    assert created_task["created_by"] == "operator"
    assert created_task["robot_id"] == "robot-sim-01"
    assert created_task["workstation_id"] == "station-a"

    list_body = list_response.json()
    list_data = _unwrap_success(list_response)
    assert list_body["meta"]["pagination"] == {
        "page": 1,
        "page_size": 10,
        "total": 1,
        "total_pages": 1,
    }
    assert len(list_data["items"]) == 1
    assert list_data["items"][0]["task_id"] == created_task["task_id"]

    detail_data = _unwrap_success(detail_response)
    assert detail_data == created_task

    chain_data = _unwrap_success(chain_response)
    assert chain_data["task"] == created_task
    assert len(chain_data["status_history"]) == 1
    assert chain_data["status_history"][0]["from_status"] is None
    assert chain_data["status_history"][0]["to_status"] == "created"
    assert chain_data["status_history"][0]["changed_by"] == "operator"
    assert chain_data["status_history"][0]["reason"] == "Task created and accepted by the API."
    assert [item["event_type"] for item in chain_data["audit_chain"]] == [
        "task_created",
        "task_status_changed",
    ]
    assert chain_data["audit_chain"][0]["status_to"] == "created"
    assert chain_data["audit_chain"][1]["payload"]["reason"] == "Task created and accepted by the API."
    assert chain_data["semantic_action_plan"] is None
    assert chain_data["execution_plan"] is None
    assert chain_data["execution_result"] is None


def test_task_create_rejects_blank_required_fields(monkeypatch) -> None:
    payload = _task_payload()
    payload["workstation_id"] = "   "

    with _build_client(monkeypatch) as client:
        _unwrap_success(_login(client, "operator", "operator-secret"))
        response = client.post("/api/tasks", json=payload)

    body = _unwrap_error(response, status_code=422, code="request.validation_error")
    assert any(
        detail["loc"] == ["body", "workstation_id"] and detail["msg"] == "Value error, must not be empty"
        for detail in body["error"]["details"]
    )


def test_task_create_requires_execution_prerequisites(monkeypatch) -> None:
    with _build_client(
        monkeypatch,
        execution_robot_config_id=None,
        safety_rule_set_id=None,
        safety_emergency_stop_enabled=False,
    ) as client:
        _unwrap_success(_login(client, "operator", "operator-secret"))
        response = client.post("/api/tasks", json=_task_payload())

    body = _unwrap_error(
        response,
        status_code=422,
        code="task.prerequisite_failed",
        message="Task creation prerequisites were not met.",
    )
    assert {item["code"] for item in body["error"]["details"]} == {
        "task.active_robot_config_missing",
        "task.safety_rule_set_missing",
        "task.emergency_stop_disabled",
    }


def test_task_endpoints_require_authentication_and_return_not_found(monkeypatch) -> None:
    with _build_client(monkeypatch) as client:
        unauthenticated_list = client.get("/api/tasks")
        unauthenticated_create = client.post("/api/tasks", json=_task_payload())

        _unwrap_success(_login(client, "operator", "operator-secret"))
        missing_detail = client.get("/api/tasks/task-does-not-exist")
        missing_chain = client.get("/api/tasks/task-does-not-exist/execution-chain")

    _unwrap_error(unauthenticated_list, status_code=401, code="auth.authentication_required")
    _unwrap_error(unauthenticated_create, status_code=401, code="auth.authentication_required")

    detail_body = _unwrap_error(
        missing_detail,
        status_code=404,
        code="task.not_found",
        message="Task 'task-does-not-exist' was not found.",
    )
    chain_body = _unwrap_error(
        missing_chain,
        status_code=404,
        code="task.not_found",
        message="Task 'task-does-not-exist' was not found.",
    )
    assert detail_body["error"]["details"]["task_id"] == "task-does-not-exist"
    assert chain_body["error"]["details"]["task_id"] == "task-does-not-exist"
