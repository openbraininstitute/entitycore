from fastapi import APIRouter

import app.service.cell_morphology
from app.routers.admin import router as admin_router

ROUTE = "cell-morphology"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.cell_morphology.read_many)
read_one = router.get("/{id_}")(app.service.cell_morphology.read_one)
create_one = router.post("")(app.service.cell_morphology.create_one)
update_one = router.patch("/{id_}")(app.service.cell_morphology.update_one)
delete_one = router.delete("/{id_}")(app.service.cell_morphology.delete_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.cell_morphology.admin_read_one)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(
    app.service.cell_morphology.admin_update_one
)
