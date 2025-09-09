from fastapi import APIRouter

import app.service.simulation_generation
from app.routers.admin import router as admin_router

ROUTE = "simulation-generation"
router = APIRouter(prefix=f"/{ROUTE}", tags=[ROUTE])

read_many = router.get("")(app.service.simulation_generation.read_many)
read_one = router.get("/{id_}")(app.service.simulation_generation.read_one)
create_one = router.post("")(app.service.simulation_generation.create_one)
delete_one = router.delete("/{id_}")(app.service.simulation_generation.delete_one)
update_one = router.patch("/{id_}")(app.service.simulation_generation.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.simulation_generation.admin_read_one
)
