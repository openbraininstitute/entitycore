from fastapi import APIRouter

import app.service.brain_atlas
from app.routers.admin import router as admin_router

ROUTE = "brain-atlas"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.brain_atlas.read_many)
read_one = router.get("/{atlas_id}")(app.service.brain_atlas.read_one)
read_many_region = router.get("/{atlas_id}/regions")(app.service.brain_atlas.read_many_region)
read_one_region = router.get("/{atlas_id}/regions/{atlas_region_id}")(
    app.service.brain_atlas.read_one_region
)

admin_read_one = admin_router.get(f"/{ROUTE}/{{atlas_id}}")(app.service.brain_atlas.admin_read_one)
