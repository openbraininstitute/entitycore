from collections.abc import Callable
from typing import Any

from fastapi import APIRouter

from app.schemas.service import AdminCrudService, UserCrudService


def register_default_user_routes(router: APIRouter, service: UserCrudService) -> None:
    """Attach standard CRUD user routes to a router using the given service."""
    router.get("")(service.read_many)
    router.get("/{id_}")(service.read_one)
    router.post("")(service.create_one)
    router.patch("/{id_}")(service.update_one)
    router.delete("/{id_}")(service.delete_one)


def register_default_admin_routes(router: APIRouter, service: AdminCrudService, route: str) -> None:
    """Attach admin-specific routes for a resource to the admin router."""
    router.get(f"/{route}")(service.admin_read_many)
    router.get(f"/{route}/{{id_}}")(service.admin_read_one)
    router.patch(f"/{route}/{{id_}}")(service.admin_update_one)


def create_user_router(
    route: str,
    service: UserCrudService,
    before_routes: list[Callable[[APIRouter], Any]] | None = None,
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
    return router
