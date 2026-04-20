from __future__ import annotations

import logging

import uvicorn

from robot_control_backend.bootstrap.logging import configure_logging
from robot_control_backend.bootstrap.settings import SettingsError, get_settings


def main() -> None:
    """Run the API server using the shared startup conventions."""
    try:
        settings = get_settings()
    except SettingsError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    configure_logging(settings)
    logger = logging.getLogger("robot_control_backend.api_server")
    logger.info(
        "Starting API server.",
        extra={
            "event": "api.starting",
            "app_name": settings.app_name,
            "app_env": settings.app_env.value,
        },
    )

    uvicorn.run(
        "robot_control_backend.api_server.app:create_app",
        factory=True,
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.reload,
        log_config=None,
    )
