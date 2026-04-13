"""Generic derivation routes."""

from fastapi import APIRouter

import app.service.derivation as service
from app.routers.admin import router as admin_router
from app.routers.types import AssociationRoute

ROUTE = AssociationRoute.derivation

router = APIRouter(
    prefix="",
    tags=["derivation"],
)

router.get("/{entity_route}/{entity_id}/derived-from")(service.read_many)
admin_router.get("/{entity_route}/{entity_id}/derived-from")(service.admin_read_many)

delete_one = router.delete(f"/{ROUTE}")(service.delete_one)
create_one = router.post(f"/{ROUTE}")(service.create_one)
