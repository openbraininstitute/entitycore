"""Generic derivation routes."""

from fastapi import APIRouter

import app.service.derivation as service
from app.routers.admin import router as admin_router
from app.routers.common import create_user_router, register_default_admin_routes
from app.routers.types import AssociationRoute

ROUTE = AssociationRoute.derivation

router = create_user_router(route=ROUTE, service=service)
register_default_admin_routes(router=admin_router, service=service, route=ROUTE)

from_router = APIRouter(
    prefix="",
    tags=[ROUTE],
)
from_router.get("/{entity_route}/{entity_id}/derived-from")(service.read_many_from_entity)
admin_router.get("/{entity_route}/{entity_id}/derived-from")(service.admin_read_many_from_entity)
