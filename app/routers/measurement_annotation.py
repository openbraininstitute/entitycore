from fastapi import APIRouter

import app.service.measurement_annotation
from app.routers.admin import router as admin_router

ROUTE = "measurement-annotation"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.measurement_annotation.read_many)
read_one = router.get("/{id_}")(app.service.measurement_annotation.read_one)
create_one = router.post("")(app.service.measurement_annotation.create_one)
delete_one = router.delete("/{id_}")(app.service.measurement_annotation.delete_one)
update_one = router.patch("/{id_}")(app.service.measurement_annotation.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.measurement_annotation.admin_read_one
)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(
    app.service.measurement_annotation.admin_update_one
)
