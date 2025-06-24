from fastapi import APIRouter

import app.service.cell_composition

router = APIRouter(
    prefix="/cell-composition",
    tags=["cell-composition"],
)

read_one = router.get("/{id_}")(app.service.cell_composition.read_one)
