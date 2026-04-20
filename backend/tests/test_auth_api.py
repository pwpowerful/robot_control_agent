from __future__ import annotations

from fastapi.testclient import TestClient

from robot_control_backend.api_server.app import create_app


def _build_client(monkeypatch) -> TestClient:
    monkeypatch.setenv("RCA_APP_ENV", "test")
    monkeypatch.setenv("RCA_LOG_FORMAT", "console")
    monkeypatch.setenv("RCA_AUTH_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("RCA_AUTH_ADMIN_PASSWORD", "admin-secret")
    monkeypatch.setenv("RCA_AUTH_OPERATOR_USERNAME", "operator")
    monkeypatch.setenv("RCA_AUTH_OPERATOR_PASSWORD", "operator-secret")
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


def test_unauthenticated_user_cannot_access_business_endpoints(monkeypatch) -> None:
    with _build_client(monkeypatch) as client:
        tasks_response = client.get("/api/tasks/_access-check")
        plans_response = client.get("/api/plans/_access-check")
        audit_response = client.get("/api/audit/_access-check")

    _unwrap_error(tasks_response, status_code=401, code="auth.authentication_required")
    _unwrap_error(plans_response, status_code=401, code="auth.authentication_required")
    _unwrap_error(audit_response, status_code=401, code="auth.authentication_required")


def test_operator_receives_http_only_cookie_and_cannot_access_admin_scopes(monkeypatch) -> None:
    with _build_client(monkeypatch) as client:
        login_response = _login(client, "operator", "operator-secret")
        me_response = client.get("/api/auth/me")
        task_response = client.get("/api/tasks/_access-check")
        plan_response = client.get("/api/plans/_access-check")
        robot_config_response = client.post("/api/config/robot/_access-check")
        audit_response = client.get("/api/audit/_access-check")

    login_data = _unwrap_success(login_response)
    assert "rca_session=" in login_response.headers["set-cookie"]
    assert "HttpOnly" in login_response.headers["set-cookie"]
    assert "SameSite=lax" in login_response.headers["set-cookie"]
    assert login_response.headers["X-API-Version"] == "v1"

    me_data = _unwrap_success(me_response)
    task_data = _unwrap_success(task_response)
    plan_data = _unwrap_success(plan_response)
    robot_config_error = _unwrap_error(robot_config_response, status_code=403, code="auth.permission_denied")
    audit_error = _unwrap_error(audit_response, status_code=403, code="auth.permission_denied")

    assert login_data["user"]["role_codes"] == ["operator"]
    assert me_data["user"]["role_codes"] == ["operator"]
    assert "tasks" in me_data["user"]["page_access"]
    assert "audit" not in me_data["user"]["page_access"]
    assert task_data["scope"] == "tasks"
    assert plan_data["scope"] == "plans"
    assert robot_config_error["error"]["details"]["required_permission"] == "robot_config:manage"
    assert audit_error["error"]["details"]["required_permission"] == "audit:read"


def test_admin_can_access_full_configuration_alert_and_audit_scopes(monkeypatch) -> None:
    with _build_client(monkeypatch) as client:
        login_response = _login(client, "admin", "admin-secret")
        plan_response = client.get("/api/plans/_access-check")
        robot_response = client.post("/api/config/robot/_access-check")
        safety_response = client.post("/api/config/safety-rules/_access-check")
        knowledge_response = client.post("/api/knowledge/items/_access-check")
        sample_response = client.post("/api/knowledge/samples/_access-check")
        alert_handle_response = client.post("/api/alerts/_handle-check")
        audit_response = client.get("/api/audit/_access-check")
        matrix_response = client.get("/api/auth/permission-matrix")

    _unwrap_success(login_response)
    _unwrap_success(plan_response)
    _unwrap_success(robot_response)
    _unwrap_success(safety_response)
    _unwrap_success(knowledge_response)
    _unwrap_success(sample_response)
    _unwrap_success(alert_handle_response)
    _unwrap_success(audit_response)
    matrix_data = _unwrap_success(matrix_response)

    assert {role["role_code"] for role in matrix_data["roles"]} == {"operator", "admin"}


def test_invalid_credentials_are_rejected(monkeypatch) -> None:
    with _build_client(monkeypatch) as client:
        response = _login(client, "operator", "wrong-secret")

    _unwrap_error(
        response,
        status_code=401,
        code="auth.invalid_credentials",
        message="Invalid username or password.",
    )


def test_logout_revokes_the_current_session(monkeypatch) -> None:
    with _build_client(monkeypatch) as client:
        login_response = _login(client, "admin", "admin-secret")
        logout_response = client.post("/api/auth/logout")
        after_logout_response = client.get("/api/tasks/_access-check")

    _unwrap_success(login_response)
    logout_data = _unwrap_success(logout_response)
    assert logout_data["status"] == "logged_out"
    _unwrap_error(after_logout_response, status_code=401, code="auth.authentication_required")
