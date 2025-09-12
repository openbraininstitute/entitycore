from fastapi import APIRouter

import app.service.electrical_recording_stimulus
from app.routers.admin import router as admin_router

ROUTE = "electrical-recording-stimulus"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.electrical_recording_stimulus.read_many)
read_one = router.get("/{id_}")(app.service.electrical_recording_stimulus.read_one)
create_one = router.post("")(app.service.electrical_recording_stimulus.create_one)
update_one = router.patch("/{id_}")(app.service.electrical_recording_stimulus.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.electrical_recording_stimulus.admin_read_one
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(
    app.service.electrical_recording_stimulus.admin_update_one
)
