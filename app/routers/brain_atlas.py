from fastapi import APIRouter

import app.service.brain_atlas

router = APIRouter(
    prefix="/brain-atlas",
    tags=["brain-atlas"],
)

read_many = router.get("")(app.service.brain_atlas.read_many)
read_one = router.get("/{atlas_id}")(app.service.brain_atlas.read_one)
read_many_region = router.get("/{atlas_id}/regions")(app.service.brain_atlas.read_many_region)
read_one_region = router.get("/{atlas_id}/regions/{atlas_region_id}")(
    app.service.brain_atlas.read_one_region
)
