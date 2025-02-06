from typing import Any

from pydantic import BaseModel

from app.errors import ApiErrorCode


class ErrorResponse(BaseModel, use_enum_values=True):
    """ErrorResponse."""

    error_code: ApiErrorCode
    message: str
    details: Any = None
