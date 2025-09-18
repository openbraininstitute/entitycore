from fastapi import APIRouter

import app.service.memodel
from app.routers.admin import router as admin_router

ROUTE = "memodel"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.memodel.read_many)
read_one = router.get("/{id_}")(app.service.memodel.read_one)
create_one = router.post("")(app.service.memodel.create_one)
update_one = router.patch("/{id_}")(app.service.memodel.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.memodel.admin_read_one)
