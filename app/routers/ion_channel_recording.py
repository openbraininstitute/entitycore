from fastapi import APIRouter

import app.service.ion_channel_recording

router = APIRouter(
    prefix="/ion-channel-recording",
    tags=["ion-channel-recording"],
)

read_many = router.get("")(app.service.ion_channel_recording.read_many)
read_one = router.get("/{id_}")(app.service.ion_channel_recording.read_one)
create_one = router.post("")(app.service.ion_channel_recording.create_one)
update_one = router.patch("/{id_}")(app.service.ion_channel_recording.update_one)
