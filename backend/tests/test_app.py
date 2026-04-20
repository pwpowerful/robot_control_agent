from __future__ import annotations

from fastapi.testclient import TestClient

from robot_control_backend.api_server.app import create_app


def test_app_exposes_openapi_and_system_endpoints(monkeypatch) -> None:
    monkeypatch.setenv("RCA_APP_ENV", "test")
    monkeypatch.setenv("RCA_LOG_FORMAT", "console")
    monkeypatch.setenv("RCA_AUTH_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("RCA_AUTH_ADMIN_PASSWORD", "admin-secret")
    monkeypatch.setenv("RCA_AUTH_OPERATOR_USERNAME", "operator")
    monkeypatch.setenv("RCA_AUTH_OPERATOR_PASSWORD", "operator-secret")

    app = create_app()

    with TestClient(app) as client:
        openapi_response = client.get("/openapi.json")
        health_response = client.get("/api/system/health")
        version_response = client.get("/api/system/version", headers={"X-Request-ID": "req-version-001"})

    assert openapi_response.status_code == 200
    assert openapi_response.json()["info"]["title"] == "robot-control-backend"
    assert {tag["name"] for tag in openapi_response.json()["tags"]} >= {
        "auth",
        "tasks",
        "plans",
        "alerts",
        "audit",
        "knowledge",
        "config",
        "system",
    }

    assert health_response.status_code == 200
    assert health_response.json()["success"] is True
    assert health_response.json()["data"]["status"] == "ok"
    assert {check["name"] for check in health_response.json()["data"]["checks"]} == {
        "settings",
        "auth_session_backend",
    }
    assert health_response.json()["meta"]["api_version"] == "v1"

    assert version_response.status_code == 200
    assert version_response.headers["X-Request-ID"] == "req-version-001"
    assert version_response.headers["X-API-Version"] == "v1"
    assert version_response.json()["success"] is True
    assert version_response.json()["meta"]["request_id"] == "req-version-001"
    assert version_response.json()["data"]["api_version"] == "v1"
    assert version_response.json()["data"]["app_version"] == "0.1.0"
