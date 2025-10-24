from fastapi import APIRouter

import app.service.circuit_extraction_execution
from app.routers.admin import router as admin_router

ROUTE = "circuit-extraction-execution"
router = APIRouter(prefix=f"/{ROUTE}", tags=[ROUTE])

read_many = router.get("")(app.service.circuit_extraction_execution.read_many)
read_one = router.get("/{id_}")(app.service.circuit_extraction_execution.read_one)
create_one = router.post("")(app.service.circuit_extraction_execution.create_one)
delete_one = router.delete("/{id_}")(app.service.circuit_extraction_execution.delete_one)
update_one = router.patch("/{id_}")(app.service.circuit_extraction_execution.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.circuit_extraction_execution.admin_read_one
)
admin_update_one = admin_router.patch("/circuit-extraction-execution/{id_}")(
    app.service.circuit_extraction_execution.admin_update_one
)
