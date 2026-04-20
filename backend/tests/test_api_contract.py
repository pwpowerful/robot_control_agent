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


def test_validation_errors_return_structured_envelope(monkeypatch) -> None:
    with _build_client(monkeypatch) as client:
        response = client.post(
            "/api/auth/login",
            json={"username": "operator"},
            headers={"X-Request-ID": "req-validation-001"},
        )

    assert response.status_code == 422
    assert response.headers["X-Request-ID"] == "req-validation-001"
    assert response.headers["X-API-Version"] == "v1"
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "request.validation_error"
    assert response.json()["error"]["message"] == "Request validation failed."
    assert response.json()["meta"]["request_id"] == "req-validation-001"
    assert response.json()["error"]["details"][0]["loc"] == ["body", "password"]


def test_unknown_api_path_returns_structured_not_found_error(monkeypatch) -> None:
    with _build_client(monkeypatch) as client:
        response = client.get("/api/not-a-real-endpoint")

    assert response.status_code == 404
    assert response.headers["X-API-Version"] == "v1"
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "resource.not_found"
    assert response.json()["error"]["message"] == "Not Found"
    assert response.json()["meta"]["request_id"]
