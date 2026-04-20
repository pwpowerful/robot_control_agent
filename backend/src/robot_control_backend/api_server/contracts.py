from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Generic, Literal, TypeVar

from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field

API_VERSION = "v1"
REQUEST_ID_HEADER = "X-Request-ID"
API_VERSION_HEADER = "X-API-Version"

PayloadT = TypeVar("PayloadT")


class ApiPayloadModel(BaseModel):
    """Base model for API payloads and envelopes."""

    model_config = ConfigDict(extra="forbid")


class PaginationMeta(ApiPayloadModel):
    """Shared pagination metadata for future list endpoints."""

    page: int = Field(ge=1, description="Current 1-based page number.")
    page_size: int = Field(ge=1, description="Maximum records returned in the current page.")
    total: int | None = Field(default=None, ge=0, description="Total records when known.")
    total_pages: int | None = Field(default=None, ge=0, description="Total page count when known.")


class ResponseMeta(ApiPayloadModel):
    """Shared response metadata returned by every API endpoint."""

    request_id: str = Field(description="Request identifier echoed in the response headers.")
    api_version: str = Field(description="Stable API contract version.")
    timestamp: datetime = Field(description="Server timestamp when the response envelope was created.")
    pagination: PaginationMeta | None = Field(default=None, description="Pagination metadata for list responses.")


class ApiSuccessResponse(ApiPayloadModel, Generic[PayloadT]):
    """Successful API response envelope."""

    success: Literal[True] = True
    data: PayloadT = Field(description="Endpoint-specific payload.")
    meta: ResponseMeta = Field(description="Envelope metadata shared by all API responses.")


class ApiErrorCode(StrEnum):
    """Canonical structured error codes for the backend API."""

    AUTHENTICATION_REQUIRED = "auth.authentication_required"
    INVALID_CREDENTIALS = "auth.invalid_credentials"
    PERMISSION_DENIED = "auth.permission_denied"
    VALIDATION_ERROR = "request.validation_error"
    NOT_FOUND = "resource.not_found"
    TASK_NOT_FOUND = "task.not_found"
    TASK_PREREQUISITE_FAILED = "task.prerequisite_failed"
    HTTP_ERROR = "request.http_error"
    NOT_IMPLEMENTED = "system.not_implemented"
    INTERNAL_ERROR = "system.internal_error"


class ApiErrorDetail(ApiPayloadModel):
    """Structured error body returned inside the error envelope."""

    code: ApiErrorCode = Field(description="Stable machine-readable error code.")
    message: str = Field(description="Human-readable summary safe to surface in the UI.")
    details: dict[str, Any] | list[dict[str, Any]] | None = Field(
        default=None,
        description="Optional structured details to help clients debug or render validation feedback.",
    )


class ApiErrorResponse(ApiPayloadModel):
    """Error API response envelope."""

    success: Literal[False] = False
    error: ApiErrorDetail = Field(description="Structured error details.")
    meta: ResponseMeta = Field(description="Envelope metadata shared by all API responses.")


_ERROR_RESPONSE_DESCRIPTIONS: dict[int, str] = {
    401: "Authentication failed or the current session is missing.",
    403: "The current user does not have permission to access the endpoint.",
    404: "The requested API resource does not exist.",
    422: "The request payload or parameters failed validation.",
    500: "The server encountered an unexpected internal error.",
    501: "The API contract reserves the endpoint, but the implementation is not available yet.",
}


def build_response_meta(request: Request, *, pagination: PaginationMeta | None = None) -> ResponseMeta:
    """Create the shared response metadata for the current request."""
    return ResponseMeta(
        request_id=get_request_id(request),
        api_version=get_api_version(request),
        timestamp=datetime.now(tz=UTC),
        pagination=pagination,
    )


def build_success_response(
    request: Request,
    data: PayloadT,
    *,
    pagination: PaginationMeta | None = None,
) -> ApiSuccessResponse[PayloadT]:
    """Wrap a payload in the shared success envelope."""
    return ApiSuccessResponse[Any](
        data=data,
        meta=build_response_meta(request, pagination=pagination),
    )


def error_responses(*status_codes: int) -> dict[int, dict[str, Any]]:
    """Build OpenAPI response documentation for structured API errors."""
    responses: dict[int, dict[str, Any]] = {}
    for status_code in status_codes:
        description = _ERROR_RESPONSE_DESCRIPTIONS.get(status_code)
        if description is None:
            raise ValueError(f"Unsupported structured error status code: {status_code}")
        responses[status_code] = {
            "model": ApiErrorResponse,
            "description": description,
        }
    return responses


def get_request_id(request: Request) -> str:
    """Resolve the current request id from request state or headers."""
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        return request_id
    incoming_request_id = request.headers.get(REQUEST_ID_HEADER, "").strip()
    return incoming_request_id or str(uuid.uuid4())


def get_api_version(request: Request) -> str:
    """Resolve the API version for the current request."""
    return getattr(request.state, "api_version", API_VERSION)
