from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from robot_control_backend.api_server.contracts import (
    API_VERSION_HEADER,
    ApiErrorCode,
    ApiErrorDetail,
    ApiErrorResponse,
    REQUEST_ID_HEADER,
    build_response_meta,
)

logger = logging.getLogger("robot_control_backend.api_server.errors")


class ApiException(Exception):
    """Application-level exception mapped to the structured API error envelope."""

    def __init__(
        self,
        *,
        status_code: int,
        code: ApiErrorCode,
        message: str,
        details: dict[str, Any] | list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers or {}


def register_exception_handlers(app: FastAPI) -> None:
    """Register the shared exception handlers for the API server."""
    app.add_exception_handler(ApiException, handle_api_exception)
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(RequestValidationError, handle_request_validation_error)
    app.add_exception_handler(Exception, handle_unexpected_exception)


async def handle_api_exception(request: Request, exc: ApiException) -> JSONResponse:
    """Render application exceptions in the shared error envelope."""
    return _render_error_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
        headers=exc.headers,
    )


async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Render framework HTTP errors in the shared error envelope."""
    message, details = _normalize_http_detail(exc.detail)
    return _render_error_response(
        request,
        status_code=exc.status_code,
        code=_map_http_error_code(exc.status_code),
        message=message,
        details=details,
        headers=exc.headers,
    )


async def handle_request_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Render FastAPI validation errors in the shared error envelope."""
    details = [
        {
            "loc": [str(item) for item in error["loc"]],
            "msg": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return _render_error_response(
        request,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code=ApiErrorCode.VALIDATION_ERROR,
        message="Request validation failed.",
        details=details,
    )


async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    """Render unexpected exceptions without leaking internal details."""
    logger.exception(
        "Unhandled API exception.",
        extra={
            "event": "api.unhandled_exception",
            "request_id": getattr(request.state, "request_id", None),
            "path": request.url.path,
            "method": request.method,
        },
    )
    return _render_error_response(
        request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code=ApiErrorCode.INTERNAL_ERROR,
        message="Internal server error.",
    )


def _render_error_response(
    request: Request,
    *,
    status_code: int,
    code: ApiErrorCode,
    message: str,
    details: dict[str, Any] | list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    meta = build_response_meta(request)
    payload = ApiErrorResponse(
        error=ApiErrorDetail(
            code=code,
            message=message,
            details=details,
        ),
        meta=meta,
    )
    response = JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
    )
    if headers:
        response.headers.update(headers)
    response.headers.setdefault(REQUEST_ID_HEADER, meta.request_id)
    response.headers.setdefault(API_VERSION_HEADER, meta.api_version)
    return response


def _map_http_error_code(status_code: int) -> ApiErrorCode:
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return ApiErrorCode.AUTHENTICATION_REQUIRED
    if status_code == status.HTTP_403_FORBIDDEN:
        return ApiErrorCode.PERMISSION_DENIED
    if status_code == status.HTTP_404_NOT_FOUND:
        return ApiErrorCode.NOT_FOUND
    if status_code == status.HTTP_501_NOT_IMPLEMENTED:
        return ApiErrorCode.NOT_IMPLEMENTED
    return ApiErrorCode.HTTP_ERROR


def _normalize_http_detail(detail: Any) -> tuple[str, dict[str, Any] | list[dict[str, Any]] | None]:
    if isinstance(detail, str):
        return detail, None
    if isinstance(detail, list):
        return "HTTP request error.", detail
    if isinstance(detail, dict):
        return "HTTP request error.", [detail]
    return "HTTP request error.", None
