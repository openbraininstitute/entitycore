from fastapi import APIRouter

import app.service.ion_channel_model

router = APIRouter(
    prefix="/ion-channel-model",
    tags=["ion-channel-model"],
)

read_many = router.get("")(app.service.ion_channel_model.read_many)
read_one = router.get("/{id_}")(app.service.ion_channel_model.read_one)
create_one = router.post("")(app.service.ion_channel_model.create_one)
