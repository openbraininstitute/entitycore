from fastapi import APIRouter

import app.service.morphology
from app.routers.admin import router as admin_router

router = APIRouter(
    prefix="/reconstruction-morphology",
    tags=["reconstruction-morphology"],
)

read_many = router.get("")(app.service.morphology.read_many)
read_one = router.get("/{id_}")(app.service.morphology.read_one)
create_one = router.post("")(app.service.morphology.create_one)
update_one = router.patch("/{id_}")(app.service.morphology.update_one)

admin_update_one = admin_router.patch("/reconstruction-morphology/{id_}")(
    app.service.morphology.admin_update_one
)
