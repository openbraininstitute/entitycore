from fastapi import APIRouter

import app.service.simulation_result
from app.routers.admin import router as admin_router

router = APIRouter(
    prefix="/simulation-result",
    tags=["simulation-result"],
)

read_many = router.get("")(app.service.simulation_result.read_many)
read_one = router.get("/{id_}")(app.service.simulation_result.read_one)
create_one = router.post("")(app.service.simulation_result.create_one)
update_one = router.patch("/{id_}")(app.service.simulation_result.update_one)

admin_update_one = admin_router.patch("/simulation-result/{id_}")(
    app.service.simulation_result.admin_update_one
)
