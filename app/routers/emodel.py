from fastapi import APIRouter

import app.service.electrical_cell_recording
import app.service.emodel
from app.routers.admin import router as admin_router

router = APIRouter(
    prefix="/emodel",
    tags=["emodel"],
)

read_many = router.get("")(app.service.emodel.read_many)
read_one = router.get("/{id_}")(app.service.emodel.read_one)
create_one = router.post("")(app.service.emodel.create_one)
update_one = router.patch("/{id_}")(app.service.emodel.update_one)

admin_update_one = admin_router.patch("/emodel/{id_}")(app.service.emodel.admin_update_one)
