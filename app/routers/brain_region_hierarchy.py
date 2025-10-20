from fastapi import APIRouter

import app.service.brain_region_hierarchy
from app.routers.admin import router as admin_router

ROUTE = "brain-region-hierarchy"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.brain_region_hierarchy.read_many)
read_one = router.get("/{id_}")(app.service.brain_region_hierarchy.read_one)
read_hierarchy = router.get("/{id_}/hierarchy")(app.service.brain_region_hierarchy.read_hierarchy)
create_one = router.post("")(app.service.brain_region_hierarchy.create_one)
update_one = router.patch("/{id_}")(app.service.brain_region_hierarchy.update_one)
delete_one = router.delete("/{id_}")(app.service.brain_region_hierarchy.delete_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.brain_region_hierarchy.read_one)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(
    app.service.brain_region_hierarchy.update_one
)
