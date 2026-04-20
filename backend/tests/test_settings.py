from __future__ import annotations

import pytest

from robot_control_backend.bootstrap.settings import SettingsError, get_settings, run_configuration_preflight


def _configure_real_robot_execution(monkeypatch) -> None:
    monkeypatch.setenv("RCA_ROBOT_ADAPTER_MODE", "real")
    monkeypatch.setenv("RCA_ROBOT_CONTROL_ENDPOINT", "https://robot.example.internal/control")
    monkeypatch.setenv("RCA_DATABASE_URL", "postgresql+psycopg://robot_user:secret@127.0.0.1:5432/robot_control")
    monkeypatch.setenv("RCA_SHARED_MODEL_API_KEY", "test-api-key")


def test_development_defaults_allow_minimal_bootstrap(monkeypatch) -> None:
    monkeypatch.delenv("RCA_APP_ENV", raising=False)
    monkeypatch.delenv("RCA_DATABASE_URL", raising=False)
    monkeypatch.delenv("RCA_SHARED_MODEL_API_KEY", raising=False)

    settings = get_settings()

    assert settings.app_env.value == "development"
    assert settings.app_host == "127.0.0.1"
    assert settings.app_port == 8000
    assert settings.log_format == "json"


def test_grouped_configuration_properties_use_safe_defaults(monkeypatch, tmp_path) -> None:
    artifact_root = tmp_path / "artifacts"
    monkeypatch.setenv("RCA_ARTIFACT_ROOT_DIR", str(artifact_root))

    settings = get_settings()

    assert settings.database.url is None
    assert settings.model_provider.provider_name.value == "shared_api"
    assert settings.model_provider.has_api_key is False
    assert settings.vision.adapter_mode.value == "simulated"
    assert settings.robot.adapter_mode.value == "simulated"
    assert settings.safety.emergency_stop_enabled is True
    assert settings.safety.max_task_duration_seconds == 60
    assert len(settings.safety.forbidden_zones) >= 1
    assert "joint_1" in settings.safety.joint_limits
    assert settings.auth.admin_username == "admin"
    assert settings.auth.admin_password_configured is True
    assert settings.auth.operator_username == "operator"
    assert settings.auth.operator_password_configured is True
    assert settings.artifacts.root_dir == artifact_root.resolve()
    assert settings.artifacts.root_dir.is_dir()


def test_production_requires_critical_configuration(monkeypatch) -> None:
    monkeypatch.setenv("RCA_APP_ENV", "production")
    monkeypatch.delenv("RCA_DATABASE_URL", raising=False)
    monkeypatch.delenv("RCA_SHARED_MODEL_API_KEY", raising=False)

    with pytest.raises(SettingsError) as exc_info:
        get_settings()

    assert "RCA_DATABASE_URL" in str(exc_info.value)
    assert "RCA_SHARED_MODEL_API_KEY" in str(exc_info.value)
    assert "RCA_AUTH_ADMIN_PASSWORD" in str(exc_info.value)
    assert "RCA_AUTH_OPERATOR_PASSWORD" in str(exc_info.value)


def test_real_execution_requires_explicit_allow_flag(monkeypatch) -> None:
    _configure_real_robot_execution(monkeypatch)
    monkeypatch.setenv("RCA_EXECUTION_ROBOT_CONFIG_ID", "robot-config-001")
    monkeypatch.setenv("RCA_SAFETY_RULE_SET_ID", "safety-default")
    monkeypatch.delenv("RCA_EXECUTION_ALLOW_REAL_HARDWARE", raising=False)

    with pytest.raises(SettingsError) as exc_info:
        get_settings()

    assert "RCA_EXECUTION_ALLOW_REAL_HARDWARE" in str(exc_info.value)


def test_real_execution_requires_robot_and_safety_configuration(monkeypatch) -> None:
    _configure_real_robot_execution(monkeypatch)
    monkeypatch.setenv("RCA_EXECUTION_ALLOW_REAL_HARDWARE", "true")
    monkeypatch.delenv("RCA_EXECUTION_ROBOT_CONFIG_ID", raising=False)
    monkeypatch.delenv("RCA_SAFETY_RULE_SET_ID", raising=False)

    with pytest.raises(SettingsError) as exc_info:
        get_settings()

    assert "RCA_EXECUTION_ROBOT_CONFIG_ID" in str(exc_info.value)
    assert "RCA_SAFETY_RULE_SET_ID" in str(exc_info.value)


def test_artifact_root_must_be_directory(monkeypatch, tmp_path) -> None:
    invalid_root = tmp_path / "artifact-root.txt"
    invalid_root.write_text("not-a-directory", encoding="utf-8")
    monkeypatch.setenv("RCA_ARTIFACT_ROOT_DIR", str(invalid_root))

    with pytest.raises(SettingsError) as exc_info:
        get_settings()

    assert "RCA_ARTIFACT_ROOT_DIR" in str(exc_info.value)


def test_database_connectivity_preflight_reports_clear_error(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("RCA_ARTIFACT_ROOT_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("RCA_DATABASE_URL", "postgresql+psycopg://robot_user:secret@127.0.0.1:1/robot_control")
    monkeypatch.setenv("RCA_DATABASE_CONNECTIVITY_CHECK", "true")
    monkeypatch.setenv("RCA_DATABASE_CONNECTIVITY_TIMEOUT_SECONDS", "1")

    settings = get_settings()

    with pytest.raises(SettingsError) as exc_info:
        run_configuration_preflight(settings)

    assert "Database connectivity preflight failed" in str(exc_info.value)
    assert "RCA_DATABASE_URL" in str(exc_info.value)
