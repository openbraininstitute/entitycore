"""Api exceptions."""

import dataclasses
from collections.abc import Iterator
from contextlib import contextmanager
from enum import StrEnum, auto
from http import HTTPStatus
from typing import Any

from psycopg2.errors import ForeignKeyViolation, InsufficientPrivilege, UniqueViolation
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, NoResultFound, ProgrammingError

from app.utils.enum import UpperStrEnum


class AuthErrorReason(StrEnum):
    """Authentication and authorization errors."""

    AUTH_TOKEN_MISSING = "The authorization token is missing"  # noqa: S105
    AUTH_TOKEN_INVALID = "The authorization token is invalid"  # noqa: S105
    AUTH_TOKEN_EXPIRED = "The authorization token is expired"  # noqa: S105
    NOT_AUTHENTICATED_USER = "User not authenticated"
    NOT_AUTHORIZED_USER = "User not authorized"
    NOT_AUTHORIZED_PROJECT = "User not authorized for the given virtual-lab-id or project-id"
    PROJECT_REQUIRED = "The headers virtual-lab-id and project-id are required"
    ADMIN_REQUIRED = "Service admin role required"
    UNKNOWN = "Unknown reason"


class ApiErrorCode(UpperStrEnum):
    """API Error codes."""

    GENERIC_ERROR = auto()
    NOT_AUTHENTICATED = auto()
    NOT_AUTHORIZED = auto()
    INVALID_REQUEST = auto()
    ENTITY_NOT_FOUND = auto()
    ENTITY_FORBIDDEN = auto()
    ENTITY_DUPLICATED = auto()
    ASSET_NOT_FOUND = auto()
    ASSET_DUPLICATED = auto()
    ASSET_INVALID_FILE = auto()
    ASSET_MISSING_PATH = auto()
    ASSET_INVALID_PATH = auto()
    ASSET_NOT_A_DIRECTORY = auto()
    ASSET_INVALID_SCHEMA = auto()
    ASSET_INVALID_CONTENT_TYPE = auto()
    ION_NAME_NOT_FOUND = auto()
    S3_CANNOT_CREATE_PRESIGNED_URL = auto()


@dataclasses.dataclass(kw_only=True)
class ApiError(Exception):
    """API Error."""

    message: str
    error_code: ApiErrorCode
    http_status_code: HTTPStatus | int = HTTPStatus.BAD_REQUEST
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


@contextmanager
def ensure_foreign_keys_integrity(
    error_message: str, error_code: ApiErrorCode = ApiErrorCode.INVALID_REQUEST
) -> Iterator[None]:
    """Context manager that raises ApiError when a ForeignKeyViolation is raised."""
    try:
        yield
    except IntegrityError as err:
        if isinstance(err.orig, ForeignKeyViolation):
            raise ApiError(
                message=error_message,
                error_code=error_code,
                http_status_code=HTTPStatus.CONFLICT,
                details=str(err),
            ) from err
        raise


@contextmanager
def ensure_authorized_references(
    error_message: str, error_code: ApiErrorCode = ApiErrorCode.INVALID_REQUEST
) -> Iterator[None]:
    """Context manager that raises ApiError when an InsufficientPrivilage error is raised."""
    try:
        yield
    except ProgrammingError as err:
        if isinstance(err.orig, InsufficientPrivilege):
            raise ApiError(
                message=error_message, error_code=error_code, http_status_code=HTTPStatus.FORBIDDEN
            ) from err
        raise


@contextmanager
def ensure_valid_schema(
    error_message: str, error_code: ApiErrorCode = ApiErrorCode.INVALID_REQUEST
) -> Iterator[None]:
    """Context manager that raises ApiError when a schema validation error is raised."""
    try:
        yield
    except ValidationError as err:
        raise ApiError(
            message=error_message,
            error_code=error_code,
            http_status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            details=[e["msg"] for e in err.errors()],
        ) from err
