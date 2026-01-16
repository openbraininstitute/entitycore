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
create_one = router.post("")(app.service.brain_atlas.create_one)
update_one = router.patch("/{id_}")(app.service.brain_atlas.update_one)
delete_one = router.delete("/{id_}")(app.service.brain_atlas.delete_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{atlas_id}}")(app.service.brain_atlas.admin_read_one)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(app.service.brain_atlas.admin_update_one)

read_many_region = router.get("/{atlas_id}/regions")(app.service.brain_atlas.read_many_region)
read_one_region = router.get("/{atlas_id}/regions/{atlas_region_id}")(
    app.service.brain_atlas.read_one_region
)
