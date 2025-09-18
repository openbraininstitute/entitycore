from fastapi import APIRouter

import app.service.ion_channel_model
from app.routers.admin import router as admin_router

ROUTE = "ion-channel-model"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.ion_channel_model.read_many)
read_one = router.get("/{id_}")(app.service.ion_channel_model.read_one)
create_one = router.post("")(app.service.ion_channel_model.create_one)
update_one = router.patch("/{id_}")(app.service.ion_channel_model.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.ion_channel_model.admin_read_one)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(
    app.service.ion_channel_model.admin_update_one
)
