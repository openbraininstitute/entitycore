from fastapi import APIRouter

import app.service.cell_morphology_protocol
from app.routers.admin import router as admin_router

ROUTE = "cell-morphology-protocol"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.cell_morphology_protocol.read_many)
read_one = router.get("/{id_}")(app.service.cell_morphology_protocol.read_one)
create_one = router.post("")(app.service.cell_morphology_protocol.create_one)
update_one = router.post("")(app.service.cell_morphology_protocol.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.cell_morphology_protocol.admin_read_one
)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(
    app.service.cell_morphology_protocol.admin_update_one
)
