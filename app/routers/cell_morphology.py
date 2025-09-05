from fastapi import APIRouter

import app.service.cell_morphology

router = APIRouter(
    prefix="/cell-morphology",
    tags=["cell-morphology"],
)

read_many = router.get("")(app.service.cell_morphology.read_many)
read_one = router.get("/{id_}")(app.service.cell_morphology.read_one)
create_one = router.post("")(app.service.cell_morphology.create_one)
