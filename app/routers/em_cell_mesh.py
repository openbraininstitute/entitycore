from fastapi import APIRouter

import app.service.em_cell_mesh

router = APIRouter(
    prefix="/em-cell-mesh",
    tags=["em-cell-mesh"],
)

read_many = router.get("")(app.service.em_cell_mesh.read_many)
read_one = router.get("/{id_}")(app.service.em_cell_mesh.read_one)
create_one = router.post("")(app.service.em_cell_mesh.create_one)
