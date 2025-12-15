from fastapi import APIRouter

import app.service.organization
from app.routers.admin import router as admin_router

ROUTE = "organization"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.organization.read_many)
read_one = router.get("/{id_}")(app.service.organization.read_one)
create_one = router.post("")(app.service.organization.create_one)
delete_one = router.delete("/{id_}")(app.service.organization.delete_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.organization.admin_read_one)
