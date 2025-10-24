from fastapi import APIRouter

import app.service.circuit_extraction_config
from app.routers.admin import router as admin_router

ROUTE = "circuit-extraction-config"
router = APIRouter(prefix=f"/{ROUTE}", tags=[ROUTE])

read_many = router.get("")(app.service.circuit_extraction_config.read_many)
read_one = router.get("/{id_}")(app.service.circuit_extraction_config.read_one)
create_one = router.post("")(app.service.circuit_extraction_config.create_one)
update_one = router.patch("/{id_}")(app.service.circuit_extraction_config.update_one)
delete_one = router.delete("/{id_}")(app.service.circuit_extraction_config.delete_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.circuit_extraction_config.admin_read_one
)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(
    app.service.circuit_extraction_config.admin_update_one
)
