from fastapi import APIRouter

import app.service.brain_region_mesh

router = APIRouter(
    prefix="/brain-region-mesh",
    tags=["brain-region-mesh"],
)

read_many = router.get("")(app.service.brain_region_mesh.read_many)
read_one = router.get("/{id_}")(app.service.brain_region_mesh.read_one)
create_one = router.post("")(app.service.brain_region_mesh.create_one)
