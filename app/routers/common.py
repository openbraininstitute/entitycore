import uuid
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter

from app.dependencies.db import SessionDep
from app.routers.types import ResourceRoute
from app.schemas.routers import DeleteResponse
from app.schemas.service import AdminCrudService, UserCrudService
from app.service import admin as admin_service


def register_default_user_routes(router: APIRouter, service: UserCrudService) -> None:
    """Attach standard CRUD user routes to a router using the given service."""
    router.get("")(service.read_many)
    router.get("/{id_}")(service.read_one)
    router.post("")(service.create_one)
    router.patch("/{id_}")(service.update_one)
    router.delete("/{id_}")(service.delete_one)


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
    before_routes: list[Callable[[APIRouter], Any]] | None = None,
    after_routes: list[Callable[[APIRouter], Any]] | None = None,
) -> APIRouter:
    """Create default APIRouter with CRUD routes."""
    router = APIRouter(
        prefix=f"/{route}",
        tags=[route],
    )
    if before_routes:
        for route_func in before_routes:
            route_func(router)

    register_default_user_routes(router=router, service=service)

    if after_routes:
        for route_func in after_routes:
            route_func(router)

    return router
