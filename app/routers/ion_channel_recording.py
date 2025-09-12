from fastapi import APIRouter

import app.service.ion_channel_recording
from app.routers.admin import router as admin_router

router = APIRouter(
    prefix="/ion-channel-recording",
    tags=["ion-channel-recording"],
)

read_many = router.get("")(app.service.ion_channel_recording.read_many)
read_one = router.get("/{id_}")(app.service.ion_channel_recording.read_one)
create_one = router.post("")(app.service.ion_channel_recording.create_one)
update_one = router.patch("/{id_}")(app.service.ion_channel_recording.update_one)

admin_update_one = admin_router.patch("/ion-channel-recording/{id_}")(
    app.service.ion_channel_recording.admin_update_one
)
