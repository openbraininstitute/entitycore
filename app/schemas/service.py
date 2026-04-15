from collections.abc import Callable
from typing import Any, Protocol


class UserCrudService(Protocol):
    read_many: Callable[..., Any]
    read_one: Callable[..., Any]
    create_one: Callable[..., Any]
    update_one: Callable[..., Any]
    delete_one: Callable[..., Any]


class AdminCrudService(Protocol):
    admin_read_many: Callable[..., Any]
    admin_read_one: Callable[..., Any]
    admin_update_one: Callable[..., Any]
