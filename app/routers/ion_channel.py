from fastapi import APIRouter

import app.service.ion_channel

router = APIRouter(
    prefix="/ion-channel",
    tags=["ion-channel"],
)

read_many = router.get("")(app.service.ion_channel.read_many)
read_one = router.get("/{id_}")(app.service.ion_channel.read_one)
create_one = router.post("")(app.service.ion_channel.create_one)
