from fastapi import APIRouter

import app.service.simulation_execution
from app.routers.admin import router as admin_router

ROUTE = "simulation-execution"
router = APIRouter(prefix=f"/{ROUTE}", tags=[ROUTE])

read_many = router.get("")(app.service.simulation_execution.read_many)
read_one = router.get("/{id_}")(app.service.simulation_execution.read_one)
create_one = router.post("")(app.service.simulation_execution.create_one)
delete_one = router.delete("/{id_}")(app.service.simulation_execution.delete_one)
update_one = router.patch("/{id_}")(app.service.simulation_execution.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.simulation_execution.admin_read_one
)
admin_update_one = admin_router.patch("/simulation-execution/{id_}")(
    app.service.simulation_execution.admin_update_one
)
