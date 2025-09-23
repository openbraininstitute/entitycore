from fastapi import APIRouter

import app.service.calibration
from app.routers.admin import router as admin_router

ROUTE = "calibration"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.calibration.read_many)
read_one = router.get("/{id_}")(app.service.calibration.read_one)
create_one = router.post("")(app.service.calibration.create_one)
delete_one = router.delete("/{id_}")(app.service.calibration.delete_one)
update_one = router.patch("/{id_}")(app.service.calibration.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.calibration.admin_read_one)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(app.service.calibration.admin_update_one)
