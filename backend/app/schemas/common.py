"""Shared Pydantic schemas — base models, error envelopes, pagination."""
from pydantic import BaseModel
from typing import Any


class ErrorResponse(BaseModel):
    """Consistent error envelope for all API errors."""
    error_code: str
    message: str
    details: dict[str, Any] | None = None


class SuccessResponse(BaseModel):
    """Generic success wrapper."""
    success: bool = True
    message: str
    data: Any | None = None


class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 50
