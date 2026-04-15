from fastapi import APIRouter

import app.service.scientific_artifact_publication_link as service
from app.routers.admin import router as admin_router
from app.routers.types import AssociationRoute

ROUTE = AssociationRoute.scientific_artifact_publication_link

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_one = router.get("/{id_}")(service.read_one)
read_many = router.get("")(service.read_many)
create_one = router.post("")(service.create_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(service.admin_read_one)
admin_read_many = admin_router.get(f"/{ROUTE}")(service.admin_read_many)
admin_delete_one = admin_router.delete(f"/{ROUTE}/{{id_}}")(service.admin_delete_one)
