from fastapi import APIRouter

import app.service.species
from app.routers.admin import router as admin_router

ROUTE = "species"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.species.read_many)
read_one = router.get("/{id_}")(app.service.species.read_one)
create_one = router.post("")(app.service.species.create_one)
update_one = router.patch("/{id_}")(app.service.species.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.species.admin_read_one)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(app.service.species.admin_update_one)
