from fastapi import APIRouter

import app.service.electrical_recording_stimulus

router = APIRouter(
    prefix="/electrical-recording-stimulus",
    tags=["electrical-recording-stimulus"],
)

read_many = router.get("")(app.service.electrical_recording_stimulus.read_many)
read_one = router.get("/{id_}")(app.service.electrical_recording_stimulus.read_one)
create_one = router.post("")(app.service.electrical_recording_stimulus.create_one)
