from __future__ import annotations

import json
import logging
import math
import os
import tempfile
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import psycopg
from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError, field_validator, model_validator
from sqlalchemy.engine import make_url

BACKEND_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ARTIFACT_ROOT = Path(tempfile.gettempdir()) / "robot-control-agent" / "artifacts"


class SettingsError(RuntimeError):
    """Raised when application configuration is missing or invalid."""


class AppEnvironment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class AdapterMode(StrEnum):
    SIMULATED = "simulated"
    REAL = "real"


class ModelProviderName(StrEnum):
    SHARED_API = "shared_api"


class ForbiddenZone(BaseModel):
    """Conservative workspace area that execution must avoid."""

    model_config = ConfigDict(frozen=True)

    name: str
    frame: str = "workspace"
    min_corner: tuple[float, float, float]
    max_corner: tuple[float, float, float]


class JointLimit(BaseModel):
    """Conservative joint envelope in degrees."""

    model_config = ConfigDict(frozen=True)

    minimum_degrees: float
    maximum_degrees: float

    @model_validator(mode="after")
    def _validate_range(self) -> JointLimit:
        if self.minimum_degrees >= self.maximum_degrees:
            raise ValueError("joint limit minimum_degrees must be less than maximum_degrees")
        return self


class DatabaseSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    url: str | None
    connectivity_check: bool
    connectivity_timeout_seconds: float


class ModelProviderSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider_name: ModelProviderName
    model_name: str
    base_url: str | None
    timeout_seconds: float
    max_retries: int
    organization: str | None
    api_key: SecretStr | None

    @property
    def has_api_key(self) -> bool:
        return self.api_key is not None


class VisionSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    adapter_mode: AdapterMode
    backend: str
    request_timeout_seconds: float
    calibration_file: Path | None


class RobotSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    adapter_mode: AdapterMode
    backend: str
    command_timeout_seconds: float
    control_endpoint: str | None
    allow_real_hardware: bool
    robot_config_id: str | None


class AuthSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    session_cookie_name: str
    session_ttl_minutes: int
    require_secure_cookies: bool
    cookie_same_site: str
    admin_username: str
    admin_password_configured: bool
    operator_username: str
    operator_password_configured: bool


class AuditSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    enabled: bool
    event_retention_days: int
    store_raw_reasoning: bool


class SafetySettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    rule_set_id: str | None
    forbidden_zones: tuple[ForbiddenZone, ...]
    joint_limits: dict[str, JointLimit]
    max_task_duration_seconds: int
    emergency_stop_enabled: bool


class ArtifactStorageSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    root_dir: Path
    auto_create: bool


def _default_forbidden_zones() -> tuple[ForbiddenZone, ...]:
    return (
        ForbiddenZone(
            name="human_access_zone",
            frame="workspace",
            min_corner=(-0.80, -0.80, -0.10),
            max_corner=(0.80, 0.80, 1.80),
        ),
        ForbiddenZone(
            name="maintenance_envelope",
            frame="workspace",
            min_corner=(-0.35, -0.35, -0.05),
            max_corner=(0.35, 0.35, 1.20),
        ),
    )


def _default_joint_limits() -> dict[str, JointLimit]:
    return {
        "joint_1": JointLimit(minimum_degrees=-150.0, maximum_degrees=150.0),
        "joint_2": JointLimit(minimum_degrees=-110.0, maximum_degrees=110.0),
        "joint_3": JointLimit(minimum_degrees=-135.0, maximum_degrees=135.0),
        "joint_4": JointLimit(minimum_degrees=-170.0, maximum_degrees=170.0),
        "joint_5": JointLimit(minimum_degrees=-120.0, maximum_degrees=120.0),
        "joint_6": JointLimit(minimum_degrees=-170.0, maximum_degrees=170.0),
    }


class Settings(BaseModel):
    """Unified backend configuration with conservative defaults."""

    model_config = ConfigDict(extra="ignore")

    app_name: str = "robot-control-backend"
    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    reload: bool = False
    log_level: str = "INFO"
    log_format: str = "json"

    database_url: str | None = None
    database_connectivity_check: bool = False
    database_connectivity_timeout_seconds: float = 3.0

    model_provider_name: ModelProviderName = ModelProviderName.SHARED_API
    shared_model_name: str = "shared-default"
    shared_model_base_url: str | None = None
    shared_model_api_key: SecretStr | None = None
    shared_model_timeout_seconds: float = 20.0
    shared_model_max_retries: int = 1
    shared_model_organization: str | None = None

    vision_adapter_mode: AdapterMode = AdapterMode.SIMULATED
    vision_backend: str = "mock_vision"
    vision_request_timeout_seconds: float = 5.0
    vision_calibration_file: Path | None = None

    robot_adapter_mode: AdapterMode = AdapterMode.SIMULATED
    robot_backend: str = "mock_robot"
    robot_command_timeout_seconds: float = 10.0
    robot_control_endpoint: str | None = None

    execution_allow_real_hardware: bool = False
    execution_robot_config_id: str | None = None

    safety_rule_set_id: str | None = None
    safety_forbidden_zones: tuple[ForbiddenZone, ...] = Field(default_factory=_default_forbidden_zones)
    safety_joint_limits: dict[str, JointLimit] = Field(default_factory=_default_joint_limits)
    safety_max_task_duration_seconds: int = 60
    safety_emergency_stop_enabled: bool = True

    auth_session_cookie_name: str = "rca_session"
    auth_session_ttl_minutes: int = 480
    auth_require_secure_cookies: bool = False
    auth_cookie_same_site: str = "lax"
    auth_admin_username: str = "admin"
    auth_admin_password: SecretStr | None = Field(default_factory=lambda: SecretStr("change-me-admin"))
    auth_operator_username: str = "operator"
    auth_operator_password: SecretStr | None = Field(default_factory=lambda: SecretStr("change-me-operator"))

    audit_enabled: bool = True
    audit_event_retention_days: int = 90
    audit_store_raw_reasoning: bool = False

    artifact_root_dir: Path = DEFAULT_ARTIFACT_ROOT
    artifact_auto_create: bool = True

    @field_validator(
        "database_url",
        "shared_model_base_url",
        "shared_model_organization",
        "robot_control_endpoint",
        "execution_robot_config_id",
        "safety_rule_set_id",
        mode="before",
    )
    @classmethod
    def _blank_string_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("app_env", "model_provider_name", "vision_adapter_mode", "robot_adapter_mode", mode="before")
    @classmethod
    def _normalize_enums(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("shared_model_api_key", "auth_admin_password", "auth_operator_password", mode="before")
    @classmethod
    def _blank_secret_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("vision_calibration_file", "artifact_root_dir", mode="before")
    @classmethod
    def _resolve_paths(cls, value: Any) -> Any:
        if value is None or value == "":
            return None
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = (BACKEND_ROOT / path).resolve()
        return path

    @field_validator("safety_forbidden_zones", mode="before")
    @classmethod
    def _parse_forbidden_zones(cls, value: Any) -> Any:
        if value is None or value == "":
            return _default_forbidden_zones()
        if isinstance(value, str):
            return json.loads(value)
        return value

    @field_validator("safety_joint_limits", mode="before")
    @classmethod
    def _parse_joint_limits(cls, value: Any) -> Any:
        if value is None or value == "":
            return _default_joint_limits()
        if isinstance(value, str):
            return json.loads(value)
        return value

    @field_validator(
        "app_name",
        "app_host",
        "shared_model_name",
        "vision_backend",
        "robot_backend",
        "auth_session_cookie_name",
        "auth_admin_username",
        "auth_operator_username",
    )
    @classmethod
    def _require_non_empty_strings(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("auth_admin_password", "auth_operator_password")
    @classmethod
    def _validate_non_empty_secrets(cls, value: SecretStr | None, info) -> SecretStr | None:
        if value is None:
            return value
        if not value.get_secret_value().strip():
            raise ValueError(f"{info.field_name} must not be empty")
        return value

    @field_validator("app_port")
    @classmethod
    def _validate_port(cls, value: int) -> int:
        if value < 1 or value > 65535:
            raise ValueError("RCA_APP_PORT must be between 1 and 65535")
        return value

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: Any) -> str:
        if isinstance(value, int):
            normalized = logging.getLevelName(value)
        else:
            normalized = str(value).strip().upper()
        valid_levels = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
        if normalized not in valid_levels:
            raise ValueError("RCA_LOG_LEVEL must be one of CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET")
        return normalized

    @field_validator("log_format")
    @classmethod
    def _normalize_log_format(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"json", "console"}:
            raise ValueError("RCA_LOG_FORMAT must be either 'json' or 'console'")
        return normalized

    @field_validator("auth_cookie_same_site")
    @classmethod
    def _normalize_same_site(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError("RCA_AUTH_COOKIE_SAME_SITE must be one of lax, strict, none")
        return normalized

    @field_validator("shared_model_base_url", "robot_control_endpoint")
    @classmethod
    def _validate_optional_urls(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            env_name = "RCA_SHARED_MODEL_BASE_URL" if info.field_name == "shared_model_base_url" else "RCA_ROBOT_CONTROL_ENDPOINT"
            raise ValueError(f"{env_name} must be a valid http(s) URL")
        return value

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            parsed = make_url(value)
        except Exception as exc:  # pragma: no cover - exact SQLAlchemy error text is not stable
            raise ValueError(f"RCA_DATABASE_URL is not a valid SQLAlchemy database URL: {exc}") from exc
        if not parsed.drivername.startswith("postgresql"):
            raise ValueError("RCA_DATABASE_URL must use a PostgreSQL SQLAlchemy URL")
        return value

    @field_validator(
        "database_connectivity_timeout_seconds",
        "shared_model_timeout_seconds",
        "vision_request_timeout_seconds",
        "robot_command_timeout_seconds",
    )
    @classmethod
    def _validate_positive_timeouts(cls, value: float, info) -> float:
        if value <= 0:
            raise ValueError(f"{info.field_name} must be greater than 0")
        return value

    @field_validator(
        "safety_max_task_duration_seconds",
        "auth_session_ttl_minutes",
        "audit_event_retention_days",
    )
    @classmethod
    def _validate_positive_integers(cls, value: int, info) -> int:
        if value <= 0:
            raise ValueError(f"{info.field_name} must be greater than 0")
        return value

    @field_validator("shared_model_max_retries")
    @classmethod
    def _validate_retries(cls, value: int) -> int:
        if value < 0:
            raise ValueError("RCA_SHARED_MODEL_MAX_RETRIES must be greater than or equal to 0")
        return value

    @field_validator("audit_store_raw_reasoning")
    @classmethod
    def _forbid_raw_reasoning_storage(cls, value: bool) -> bool:
        if value:
            raise ValueError("RCA_AUDIT_STORE_RAW_REASONING must remain false")
        return value

    @model_validator(mode="after")
    def _validate_cross_field_rules(self) -> Settings:
        errors: list[str] = []

        if self.app_env == AppEnvironment.PRODUCTION:
            if not self.database_url:
                errors.append("RCA_DATABASE_URL is required in production.")
            if self.shared_model_api_key is None:
                errors.append("RCA_SHARED_MODEL_API_KEY is required in production.")
            if self.auth_admin_password is None or self.auth_admin_password.get_secret_value() == "change-me-admin":
                errors.append("RCA_AUTH_ADMIN_PASSWORD must be set to a non-default value in production.")
            if self.auth_operator_password is None or self.auth_operator_password.get_secret_value() == "change-me-operator":
                errors.append("RCA_AUTH_OPERATOR_PASSWORD must be set to a non-default value in production.")
            if self.reload:
                errors.append("RCA_RELOAD must remain false in production.")

        if self.auth_admin_username == self.auth_operator_username:
            errors.append("RCA_AUTH_ADMIN_USERNAME and RCA_AUTH_OPERATOR_USERNAME must be different.")

        if self.real_execution_requested:
            if not self.execution_allow_real_hardware:
                errors.append("RCA_EXECUTION_ALLOW_REAL_HARDWARE must be true before entering the real execution chain.")
            if not self.database_url:
                errors.append("RCA_DATABASE_URL is required before entering the real execution chain.")
            if self.shared_model_api_key is None:
                errors.append("RCA_SHARED_MODEL_API_KEY is required before entering the real execution chain.")
            if not self.execution_robot_config_id:
                errors.append("RCA_EXECUTION_ROBOT_CONFIG_ID is required before entering the real execution chain.")
            if not self.safety_rule_set_id:
                errors.append("RCA_SAFETY_RULE_SET_ID is required before entering the real execution chain.")
            if not self.safety_emergency_stop_enabled:
                errors.append("RCA_SAFETY_EMERGENCY_STOP_ENABLED must be true before entering the real execution chain.")
            if self.robot_adapter_mode == AdapterMode.REAL and not self.robot_control_endpoint:
                errors.append("RCA_ROBOT_CONTROL_ENDPOINT is required when RCA_ROBOT_ADAPTER_MODE=real.")
            if self.vision_adapter_mode == AdapterMode.REAL:
                if self.vision_calibration_file is None:
                    errors.append("RCA_VISION_CALIBRATION_FILE is required when RCA_VISION_ADAPTER_MODE=real.")
                elif not self.vision_calibration_file.is_file():
                    errors.append("RCA_VISION_CALIBRATION_FILE must point to an existing calibration file.")

        try:
            self.artifact_root_dir = _ensure_writable_directory(self.artifact_root_dir, auto_create=self.artifact_auto_create)
        except ValueError as exc:
            errors.append(str(exc))

        if errors:
            raise ValueError(" ".join(errors))
        return self

    @property
    def real_execution_requested(self) -> bool:
        return self.robot_adapter_mode == AdapterMode.REAL or self.vision_adapter_mode == AdapterMode.REAL

    @property
    def database(self) -> DatabaseSettings:
        return DatabaseSettings(
            url=self.database_url,
            connectivity_check=self.database_connectivity_check,
            connectivity_timeout_seconds=self.database_connectivity_timeout_seconds,
        )

    @property
    def model_provider(self) -> ModelProviderSettings:
        return ModelProviderSettings(
            provider_name=self.model_provider_name,
            model_name=self.shared_model_name,
            base_url=self.shared_model_base_url,
            timeout_seconds=self.shared_model_timeout_seconds,
            max_retries=self.shared_model_max_retries,
            organization=self.shared_model_organization,
            api_key=self.shared_model_api_key,
        )

    @property
    def vision(self) -> VisionSettings:
        return VisionSettings(
            adapter_mode=self.vision_adapter_mode,
            backend=self.vision_backend,
            request_timeout_seconds=self.vision_request_timeout_seconds,
            calibration_file=self.vision_calibration_file,
        )

    @property
    def robot(self) -> RobotSettings:
        return RobotSettings(
            adapter_mode=self.robot_adapter_mode,
            backend=self.robot_backend,
            command_timeout_seconds=self.robot_command_timeout_seconds,
            control_endpoint=self.robot_control_endpoint,
            allow_real_hardware=self.execution_allow_real_hardware,
            robot_config_id=self.execution_robot_config_id,
        )

    @property
    def auth(self) -> AuthSettings:
        return AuthSettings(
            session_cookie_name=self.auth_session_cookie_name,
            session_ttl_minutes=self.auth_session_ttl_minutes,
            require_secure_cookies=self.auth_require_secure_cookies,
            cookie_same_site=self.auth_cookie_same_site,
            admin_username=self.auth_admin_username,
            admin_password_configured=self.auth_admin_password is not None,
            operator_username=self.auth_operator_username,
            operator_password_configured=self.auth_operator_password is not None,
        )

    @property
    def audit(self) -> AuditSettings:
        return AuditSettings(
            enabled=self.audit_enabled,
            event_retention_days=self.audit_event_retention_days,
            store_raw_reasoning=self.audit_store_raw_reasoning,
        )

    @property
    def safety(self) -> SafetySettings:
        return SafetySettings(
            rule_set_id=self.safety_rule_set_id,
            forbidden_zones=self.safety_forbidden_zones,
            joint_limits=self.safety_joint_limits,
            max_task_duration_seconds=self.safety_max_task_duration_seconds,
            emergency_stop_enabled=self.safety_emergency_stop_enabled,
        )

    @property
    def artifacts(self) -> ArtifactStorageSettings:
        return ArtifactStorageSettings(
            root_dir=self.artifact_root_dir,
            auto_create=self.artifact_auto_create,
        )

    def safe_summary(self) -> dict[str, Any]:
        """Return a summary suitable for logs and config inspection."""
        return {
            "app_name": self.app_name,
            "app_env": self.app_env.value,
            "app_host": self.app_host,
            "app_port": self.app_port,
            "reload": self.reload,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "database_configured": self.database_url is not None,
            "database_connectivity_check": self.database_connectivity_check,
            "model_provider_name": self.model_provider_name.value,
            "shared_model_name": self.shared_model_name,
            "shared_model_base_url": self.shared_model_base_url or "<provider-default>",
            "shared_model_api_key_configured": self.shared_model_api_key is not None,
            "vision_adapter_mode": self.vision_adapter_mode.value,
            "vision_backend": self.vision_backend,
            "robot_adapter_mode": self.robot_adapter_mode.value,
            "robot_backend": self.robot_backend,
            "execution_allow_real_hardware": self.execution_allow_real_hardware,
            "execution_robot_config_id": self.execution_robot_config_id or "<unset>",
            "safety_rule_set_id": self.safety_rule_set_id or "<unset>",
            "safety_emergency_stop_enabled": self.safety_emergency_stop_enabled,
            "artifact_root_dir": str(self.artifact_root_dir),
            "artifact_auto_create": self.artifact_auto_create,
            "auth_admin_username": self.auth_admin_username,
            "auth_admin_password_configured": self.auth_admin_password is not None,
            "auth_operator_username": self.auth_operator_username,
            "auth_operator_password_configured": self.auth_operator_password is not None,
            "auth_require_secure_cookies": self.auth_require_secure_cookies,
        }


ENV_FIELD_MAP = {
    "app_name": "RCA_APP_NAME",
    "app_env": "RCA_APP_ENV",
    "app_host": "RCA_APP_HOST",
    "app_port": "RCA_APP_PORT",
    "reload": "RCA_RELOAD",
    "log_level": "RCA_LOG_LEVEL",
    "log_format": "RCA_LOG_FORMAT",
    "database_url": "RCA_DATABASE_URL",
    "database_connectivity_check": "RCA_DATABASE_CONNECTIVITY_CHECK",
    "database_connectivity_timeout_seconds": "RCA_DATABASE_CONNECTIVITY_TIMEOUT_SECONDS",
    "model_provider_name": "RCA_MODEL_PROVIDER_NAME",
    "shared_model_name": "RCA_SHARED_MODEL_NAME",
    "shared_model_base_url": "RCA_SHARED_MODEL_BASE_URL",
    "shared_model_api_key": "RCA_SHARED_MODEL_API_KEY",
    "shared_model_timeout_seconds": "RCA_SHARED_MODEL_TIMEOUT_SECONDS",
    "shared_model_max_retries": "RCA_SHARED_MODEL_MAX_RETRIES",
    "shared_model_organization": "RCA_SHARED_MODEL_ORGANIZATION",
    "vision_adapter_mode": "RCA_VISION_ADAPTER_MODE",
    "vision_backend": "RCA_VISION_BACKEND",
    "vision_request_timeout_seconds": "RCA_VISION_REQUEST_TIMEOUT_SECONDS",
    "vision_calibration_file": "RCA_VISION_CALIBRATION_FILE",
    "robot_adapter_mode": "RCA_ROBOT_ADAPTER_MODE",
    "robot_backend": "RCA_ROBOT_BACKEND",
    "robot_command_timeout_seconds": "RCA_ROBOT_COMMAND_TIMEOUT_SECONDS",
    "robot_control_endpoint": "RCA_ROBOT_CONTROL_ENDPOINT",
    "execution_allow_real_hardware": "RCA_EXECUTION_ALLOW_REAL_HARDWARE",
    "execution_robot_config_id": "RCA_EXECUTION_ROBOT_CONFIG_ID",
    "safety_rule_set_id": "RCA_SAFETY_RULE_SET_ID",
    "safety_forbidden_zones": "RCA_SAFETY_FORBIDDEN_ZONES",
    "safety_joint_limits": "RCA_SAFETY_JOINT_LIMITS",
    "safety_max_task_duration_seconds": "RCA_SAFETY_MAX_TASK_DURATION_SECONDS",
    "safety_emergency_stop_enabled": "RCA_SAFETY_EMERGENCY_STOP_ENABLED",
    "auth_session_cookie_name": "RCA_AUTH_SESSION_COOKIE_NAME",
    "auth_session_ttl_minutes": "RCA_AUTH_SESSION_TTL_MINUTES",
    "auth_require_secure_cookies": "RCA_AUTH_REQUIRE_SECURE_COOKIES",
    "auth_cookie_same_site": "RCA_AUTH_COOKIE_SAME_SITE",
    "auth_admin_username": "RCA_AUTH_ADMIN_USERNAME",
    "auth_admin_password": "RCA_AUTH_ADMIN_PASSWORD",
    "auth_operator_username": "RCA_AUTH_OPERATOR_USERNAME",
    "auth_operator_password": "RCA_AUTH_OPERATOR_PASSWORD",
    "audit_enabled": "RCA_AUDIT_ENABLED",
    "audit_event_retention_days": "RCA_AUDIT_EVENT_RETENTION_DAYS",
    "audit_store_raw_reasoning": "RCA_AUDIT_STORE_RAW_REASONING",
    "artifact_root_dir": "RCA_ARTIFACT_ROOT_DIR",
    "artifact_auto_create": "RCA_ARTIFACT_AUTO_CREATE",
}


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    return {key: value for key, value in dotenv_values(path).items() if value is not None}


def _resolve_bootstrap_environment(base_env: dict[str, str], process_env: dict[str, str]) -> AppEnvironment:
    env_value = process_env.get("RCA_APP_ENV") or base_env.get("RCA_APP_ENV") or AppEnvironment.DEVELOPMENT.value
    try:
        return AppEnvironment(env_value.strip().lower())
    except ValueError as exc:
        expected = ", ".join(item.value for item in AppEnvironment)
        raise SettingsError(f"RCA_APP_ENV must be one of: {expected}") from exc


def _read_raw_settings() -> dict[str, Any]:
    base_env = _load_env_file(BACKEND_ROOT / ".env")
    app_env = _resolve_bootstrap_environment(base_env=base_env, process_env=os.environ)
    env_specific = _load_env_file(BACKEND_ROOT / f".env.{app_env.value}")

    merged: dict[str, str] = {}
    merged.update(base_env)
    merged.update(env_specific)
    merged.update(os.environ)

    raw_settings: dict[str, Any] = {}
    for field_name, env_name in ENV_FIELD_MAP.items():
        if env_name in merged:
            raw_settings[field_name] = merged[env_name]

    raw_settings["app_env"] = merged.get("RCA_APP_ENV", app_env.value)
    return raw_settings


def _ensure_writable_directory(path: Path, *, auto_create: bool) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.exists() and not resolved.is_dir():
        raise ValueError("RCA_ARTIFACT_ROOT_DIR must point to a directory, not a file.")
    if not resolved.exists():
        if not auto_create:
            raise ValueError("RCA_ARTIFACT_ROOT_DIR does not exist and RCA_ARTIFACT_AUTO_CREATE is false.")
        resolved.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryFile(dir=resolved):
            pass
    except OSError as exc:
        raise ValueError(f"RCA_ARTIFACT_ROOT_DIR is not writable: {resolved} ({exc})") from exc
    return resolved


def _format_validation_error(exc: ValidationError) -> str:
    messages: list[str] = []
    for error in exc.errors():
        location = ".".join(str(item) for item in error.get("loc", ())) or "settings"
        message = error.get("msg", "invalid value")
        messages.append(f"{location}: {message}")
    return " ".join(messages)


def load_settings() -> Settings:
    """Load and validate settings without using the cache."""
    try:
        return Settings.model_validate(_read_raw_settings())
    except SettingsError:
        raise
    except ValidationError as exc:
        raise SettingsError(_format_validation_error(exc)) from exc


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached settings instance."""
    return load_settings()


def reset_settings_cache() -> None:
    """Clear the cached settings instance for tests and reloads."""
    get_settings.cache_clear()


def check_database_connectivity(settings: Settings) -> None:
    """Optionally verify that the configured PostgreSQL endpoint is reachable."""
    if not settings.database_connectivity_check:
        return
    if not settings.database_url:
        raise SettingsError("RCA_DATABASE_URL is required when RCA_DATABASE_CONNECTIVITY_CHECK=true.")

    try:
        parsed = make_url(settings.database_url)
        conninfo = parsed.set(drivername="postgresql").render_as_string(hide_password=False)
        timeout_seconds = max(1, math.ceil(settings.database_connectivity_timeout_seconds))
        with psycopg.connect(conninfo, connect_timeout=timeout_seconds) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
    except Exception as exc:
        raise SettingsError(f"Database connectivity preflight failed for RCA_DATABASE_URL: {exc}") from exc


def run_configuration_preflight(settings: Settings) -> list[str]:
    """Run optional preflight checks and return human-readable results."""
    results = [f"artifact_root_dir writable: {settings.artifact_root_dir}"]
    if settings.database_connectivity_check:
        check_database_connectivity(settings)
        results.append(
            "database connectivity check passed "
            f"(timeout={settings.database_connectivity_timeout_seconds}s)"
        )
    else:
        results.append("database connectivity check skipped")
    return results
