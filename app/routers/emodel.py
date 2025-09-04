from fastapi import APIRouter

import app.service.electrical_cell_recording
import app.service.emodel

router = APIRouter(
    prefix="/emodel",
    tags=["emodel"],
)

read_many = router.get("")(app.service.emodel.read_many)
read_one = router.get("/{id_}")(app.service.emodel.read_one)
create_one = router.post("")(app.service.emodel.create_one)
update_one = router.patch("/{id_}")(app.service.emodel.update_one)
