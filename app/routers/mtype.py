from fastapi import APIRouter

import app.service.mtype
from app.routers.admin import router as admin_router

ROUTE = "mtype"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.mtype.read_many)
read_one = router.get("/{id_}")(app.service.mtype.read_one)
create_one = router.post("")(app.service.mtype.create_one)
update_one = router.patch("/{id_}")(app.service.mtype.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.mtype.admin_read_one)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(app.service.mtype.admin_update_one)
