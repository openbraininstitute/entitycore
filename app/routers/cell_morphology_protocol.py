from fastapi import APIRouter

import app.service.cell_morphology_protocol

router = APIRouter(
    prefix="/cell-morphology-protocol",
    tags=["cell-morphology-protocol"],
)

read_many = router.get("")(app.service.cell_morphology_protocol.read_many)
read_one = router.get("/{id_}")(app.service.cell_morphology_protocol.read_one)
create_one = router.post("")(app.service.cell_morphology_protocol.create_one)
