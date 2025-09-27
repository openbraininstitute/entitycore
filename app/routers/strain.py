from fastapi import APIRouter

import app.service.strain
from app.routers.admin import router as admin_router

ROUTE = "strain"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.strain.read_many)
read_one = router.get("/{id_}")(app.service.strain.read_one)
create_one = router.post("")(app.service.strain.create_one)
update_one = router.patch("/{id_}")(app.service.strain.update_one)
delete_one = router.delete("/{id_}")(app.service.strain.delete_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.strain.admin_read_one)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(app.service.strain.admin_update_one)
