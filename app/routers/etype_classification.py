from fastapi import APIRouter

import app.service.etype_classification as service
from app.routers.admin import router as admin_router
from app.routers.types import AssociationRoute

# TODO: Implement rest of endpoints and use common router
ROUTE = AssociationRoute.etype_classification

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

create_one = router.post("")(service.create_one)
read_one = router.get("/{id_}")(service.read_one)
read_many = router.get("")(service.read_many)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(service.admin_read_one)
admin_read_many = admin_router.get(f"/{ROUTE}")(service.admin_read_many)
admin_delete_one = admin_router.delete(f"/{ROUTE}/{{id_}}")(service.admin_delete_one)
