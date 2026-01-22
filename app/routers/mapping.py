from fastapi import APIRouter

import app.service.mapping
from app.routers.admin import router as admin_router

ROUTE = "mapping"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.mapping.read_many)
read_one = router.get("/{id_}")(app.service.mapping.read_one)
create_one = router.post("")(app.service.mapping.create_one)
update_one = router.patch("/{id_}")(app.service.mapping.update_one)
delete_one = router.delete("/{id_}")(app.service.mapping.delete_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.mapping.admin_read_one)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(app.service.mapping.admin_update_one)
