"""Api exceptions."""

import dataclasses
from collections.abc import Iterator
from contextlib import contextmanager
from enum import auto
from http import HTTPStatus
from typing import Any

from psycopg2.errors import UniqueViolation, RaiseException
from sqlalchemy.exc import IntegrityError, NoResultFound

from app.utils.enum import UpperStrEnum


class ApiErrorCode(UpperStrEnum):
    """API Error codes."""

    INVALID_REQUEST = auto()
    ENTITY_NOT_FOUND = auto()
    ENTITY_FORBIDDEN = auto()
    ENTITY_DUPLICATED = auto()
    ASSET_NOT_FOUND = auto()
    ASSET_DUPLICATED = auto()


class PostgresInternalErrorCode(UpperStrEnum):
    UNAUTHORIZED_PRIVATE_REFERENCE = auto()


@dataclasses.dataclass(kw_only=True)
class ApiError(Exception):
    """API Error."""

    message: str
    error_code: ApiErrorCode
    http_status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    details: Any = None

    def __repr__(self) -> str:
        """Return the repr of the error."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code}, "
            f"http_status_code={self.http_status_code}, "
            f"details={self.details!r})"
        )

    def __str__(self) -> str:
        """Return the str representation."""
        return (
            f"message={self.message!r} "
            f"error_code={self.error_code} "
            f"http_status_code={self.http_status_code} "
            f"details={self.details!r}"
        )


@contextmanager
def ensure_result(
    error_message: str, error_code: ApiErrorCode = ApiErrorCode.ENTITY_NOT_FOUND
) -> Iterator[None]:
    """Context manager that raises ApiError when no results are found after executing a query."""
    try:
        yield
    except NoResultFound as err:
        raise ApiError(
            message=error_message,
            error_code=error_code,
            http_status_code=HTTPStatus.NOT_FOUND,
        ) from err


@contextmanager
def ensure_uniqueness(
    error_message: str, error_code: ApiErrorCode = ApiErrorCode.ENTITY_DUPLICATED
) -> Iterator[None]:
    """Context manager that raises ApiError when a UniqueViolation is raised."""
    try:
        yield
    except IntegrityError as err:
        if isinstance(err.orig, UniqueViolation):
            raise ApiError(
                message=error_message,
                error_code=error_code,
                http_status_code=HTTPStatus.CONFLICT,
            ) from err
        raise
