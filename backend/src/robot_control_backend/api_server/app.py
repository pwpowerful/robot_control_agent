from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI

from robot_control_backend import __version__
from robot_control_backend.api_server.contracts import API_VERSION, API_VERSION_HEADER, REQUEST_ID_HEADER
from robot_control_backend.api_server.errors import register_exception_handlers
from robot_control_backend.api_server.routers import API_ROUTERS, OPENAPI_TAGS
from robot_control_backend.auth.service import BootstrapAuthService
from robot_control_backend.bootstrap.logging import configure_logging
from robot_control_backend.bootstrap.settings import get_settings
from robot_control_backend.task_service.service import InMemoryTaskService


def create_app() -> FastAPI:
    """Create the FastAPI application with shared startup conventions."""
    settings = get_settings()
    configure_logging(settings)
    logger = logging.getLogger("robot_control_backend.api_server")

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        logger.info(
            "API server startup complete.",
            extra={
                "event": "api.startup",
                "app_name": settings.app_name,
                "app_env": settings.app_env.value,
            },
        )
        yield
        logger.info(
            "API server shutdown complete.",
            extra={
                "event": "api.shutdown",
                "app_name": settings.app_name,
                "app_env": settings.app_env.value,
            },
        )

    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
    )
    application.state.settings = settings
    application.state.auth_service = BootstrapAuthService(settings)
    application.state.task_service = InMemoryTaskService(settings)
    application.state.api_version = API_VERSION
    register_exception_handlers(application)

    @application.middleware("http")
    async def attach_request_context(request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER, "").strip() or str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.api_version = API_VERSION

        response = await call_next(request)
        response.headers.setdefault(REQUEST_ID_HEADER, request_id)
        response.headers.setdefault(API_VERSION_HEADER, API_VERSION)
        return response

    for router in API_ROUTERS:
        application.include_router(router)
    return application
