from fastapi import APIRouter

import app.service.em_cell_mesh
from app.routers.admin import router as admin_router

ROUTE = "em-cell-mesh"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.em_cell_mesh.read_many)
read_one = router.get("/{id_}")(app.service.em_cell_mesh.read_one)
create_one = router.post("")(app.service.em_cell_mesh.create_one)
update_one = router.patch("/{id_}")(app.service.em_cell_mesh.update_one)
delete_one = router.delete("/{id_}")(app.service.em_cell_mesh.delete_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.em_cell_mesh.admin_read_one)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(
    app.service.em_cell_mesh.admin_update_one
)
