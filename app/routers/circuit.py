from fastapi import APIRouter

import app.service.circuit
import app.service.hierarchy
from app.routers.admin import router as admin_router

ROUTE = "circuit"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

hierarchy = router.get("/hierarchy")(app.service.hierarchy.read_circuit_hierarchy)
read_many = router.get("")(app.service.circuit.read_many)
read_one = router.get("/{id_}")(app.service.circuit.read_one)
create_one = router.post("")(app.service.circuit.create_one)
update_one = router.patch("/{id_}")(app.service.circuit.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.circuit.admin_read_one)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(app.service.circuit.admin_update_one)
