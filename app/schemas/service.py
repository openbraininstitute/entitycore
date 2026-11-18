from collections.abc import Callable
from typing import Any, Protocol


class UserReadService(Protocol):
    """Service with the user read operations, the minimum for a user router."""

    read_many: Callable[..., Any]
    read_one: Callable[..., Any]


class AdminCrudService(Protocol):
    admin_read_many: Callable[..., Any]
    admin_read_one: Callable[..., Any]
    admin_create_one: Callable[..., Any]
    admin_update_one: Callable[..., Any]
