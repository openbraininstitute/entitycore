from fastapi import APIRouter

import app.service.electrical_cell_recording
from app.routers.admin import router as admin_router

ROUTE = "electrical-cell-recording"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.electrical_cell_recording.read_many)
read_one = router.get("/{id_}")(app.service.electrical_cell_recording.read_one)
create_one = router.post("")(app.service.electrical_cell_recording.create_one)
update_one = router.patch("/{id_}")(app.service.electrical_cell_recording.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.electrical_cell_recording.admin_read_one
)
