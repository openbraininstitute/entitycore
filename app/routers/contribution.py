from fastapi import APIRouter

import app.service.contribution as service
from app.routers.admin import router as admin_router
from app.routers.types import AssociationRoute

ROUTE = AssociationRoute.contribution

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(service.read_many)
read_one = router.get("/{id_}")(service.read_one)
create_one = router.post("")(service.create_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(service.admin_read_one)
admin_read_many = admin_router.get(f"/{ROUTE}")(service.admin_read_many)
