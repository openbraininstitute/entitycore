from fastapi import APIRouter

import app.service.license
from app.routers.admin import router as admin_router

ROUTE = "license"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.license.read_many)
read_one = router.get("/{id_}")(app.service.license.read_one)
create_one = router.post("")(app.service.license.create_one)
update_one = router.patch("/{id_}")(app.service.license.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.license.admin_read_one)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(app.service.license.admin_update_one)
