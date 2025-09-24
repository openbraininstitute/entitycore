from fastapi import APIRouter

import app.service.publication
from app.routers.admin import router as admin_router

ROUTE = "publication"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_one = router.get("/{id_}")(app.service.publication.read_one)
read_many = router.get("")(app.service.publication.read_many)
create_one = router.post("")(app.service.publication.create_one)
update_one = router.patch("/{id_}")(app.service.publication.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.publication.admin_read_one)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(app.service.publication.admin_update_one)
