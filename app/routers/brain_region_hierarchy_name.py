from fastapi import APIRouter

import app.service.brain_region_hierarchy_name

router = APIRouter(
    prefix="/brain-region-hierarchy-name",
    tags=["brain-region-hierarchy-name"],
)

read_many = router.get("")(app.service.brain_region_hierarchy_name.read_many)
read_one = router.get("/{id_}")(app.service.brain_region_hierarchy_name.read_one)
read_hierarchy_name_hierarchy = router.get("/{id_}/hierarchy")(
    app.service.brain_region_hierarchy_name.read_hierarchy_name_hierarchy
)
