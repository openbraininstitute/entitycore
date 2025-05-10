from fastapi import APIRouter

import app.service.brain_region_hierarchy

router = APIRouter(
    prefix="/brain-region-hierarchy",
    tags=["brain-region-hierarchy"],
)

read_many = router.get("")(app.service.brain_region_hierarchy.read_many)
read_one = router.get("/{id_}")(app.service.brain_region_hierarchy.read_one)
read_hierarchy = router.get("/{id_}/hierarchy")(app.service.brain_region_hierarchy.read_hierarchy)
