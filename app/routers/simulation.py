from fastapi import APIRouter

import app.service.simulation
from app.routers.admin import router as admin_router

router = APIRouter(
    prefix="/simulation",
    tags=["simulation"],
)

read_many = router.get("")(app.service.simulation.read_many)
read_one = router.get("/{id_}")(app.service.simulation.read_one)
create_one = router.post("")(app.service.simulation.create_one)
update_one = router.patch("/{id_}")(app.service.simulation.update_one)

admin_update_one = admin_router.patch("/simulation/{id_}")(app.service.simulation.admin_update_one)
