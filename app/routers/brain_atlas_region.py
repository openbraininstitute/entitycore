from fastapi import APIRouter

import app.service.brain_atlas_region
from app.routers.admin import router as admin_router

ROUTE = "brain-atlas-region"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.brain_atlas_region.read_many)
read_one = router.get("/{id_}")(app.service.brain_atlas_region.read_one)
create_one = router.post("")(app.service.brain_atlas_region.create_one)
update_one = router.patch("/{id_}")(app.service.brain_atlas_region.update_one)
delete_one = router.delete("/{id_}")(app.service.brain_atlas_region.delete_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.brain_atlas_region.admin_read_one
)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(
    app.service.brain_atlas_region.admin_update_one
)
