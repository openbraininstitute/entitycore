"""Generic derivation routes."""

from fastapi import APIRouter

import app.service.derivation

router = APIRouter(
    prefix="",
    tags=["derivation"],
)

router.get("/{entity_route}/{entity_id}/derived-from")(app.service.derivation.read_many)
delete_one = router.delete("/derivation")(app.service.derivation.delete_one)
create_one = router.post("/derivation")(app.service.derivation.create_one)
