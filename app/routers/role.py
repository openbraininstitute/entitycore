from fastapi import APIRouter

import app.service.role
from app.routers.admin import router as admin_router

ROUTE = "role"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.role.read_many)
read_one = router.get("/{id_}")(app.service.role.read_one)
create_one = router.post("")(app.service.role.create_one)
update_one = router.patch("/{id_}")(app.service.role.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.role.admin_read_one)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(app.service.role.admin_update_one)
