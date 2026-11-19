import uuid
from collections.abc import Callable, Collection
from enum import StrEnum, auto
from typing import Any

from fastapi import APIRouter

from app.dependencies.db import SessionDep
from app.schemas.routers import DeleteResponse
from app.schemas.service import AdminCrudService, UserCrudService
from app.service import admin as admin_service
from app.types import ResourceRoute


class UserOperation(StrEnum):
    """Default user operations, named like the service functions implementing them."""

    read_many = auto()
    read_one = auto()
    create_one = auto()
    update_one = auto()
    delete_one = auto()


# HTTP method and path of each operation, relative to the router prefix
USER_OPERATION_ROUTES: dict[UserOperation, tuple[str, str]] = {
    UserOperation.read_many: ("GET", ""),
    UserOperation.read_one: ("GET", "/{id_}"),
    UserOperation.create_one: ("POST", ""),
    UserOperation.update_one: ("PATCH", "/{id_}"),
    UserOperation.delete_one: ("DELETE", "/{id_}"),
}


def register_default_user_routes(
    router: APIRouter,
    service: UserCrudService,
    operations: Collection[UserOperation] = frozenset(UserOperation),
) -> None:
    """Attach standard CRUD user routes to a router using the given service.

    Args:
        router: the router of the resource.
        service: the service module implementing the operations.
        operations: the operations to register, all of them by default. The routes are
            registered in the order of `UserOperation`, independently of the given order.
    """
    for operation in UserOperation:
        if operation in operations:
            method, path = USER_OPERATION_ROUTES[operation]
            router.api_route(path, methods=[method])(getattr(service, operation))


def register_default_admin_routes(
    router: APIRouter, service: AdminCrudService, route: ResourceRoute
) -> None:
    """Attach admin-specific routes for a resource to the admin router."""

    def admin_delete_one(
        db: SessionDep,
        id_: uuid.UUID,
    ) -> DeleteResponse:
        return admin_service.delete_one(db=db, route=route, id_=id_)

    router.get(f"/{route}")(service.admin_read_many)
    router.get(f"/{route}/{{id_}}")(service.admin_read_one)
    router.patch(f"/{route}/{{id_}}")(service.admin_update_one)
    router.delete(f"/{route}/{{id_}}")(admin_delete_one)


def create_user_router(
    route: str,
    service: UserCrudService,
    *,
    operations: Collection[UserOperation] = frozenset(UserOperation),
    before_routes: list[Callable[[APIRouter], Any]] | None = None,
    after_routes: list[Callable[[APIRouter], Any]] | None = None,
) -> APIRouter:
    """Create default APIRouter with CRUD routes.

    Args:
        route: the route of the resource, used as prefix and tag.
        service: the service module implementing the operations.
        operations: the default user operations to register, all of them by default.
            Resources whose writes are reserved to admins register only the read operations,
            and expose the writes through the admin routes.
        before_routes: functions adding routes before the default ones.
        after_routes: functions adding routes after the default ones.
    """
    router = APIRouter(
        prefix=f"/{route}",
        tags=[route],
    )
    if before_routes:
        for route_func in before_routes:
            route_func(router)

    register_default_user_routes(router=router, service=service, operations=operations)

    if after_routes:
        for route_func in after_routes:
            route_func(router)

    return router
