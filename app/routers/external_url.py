from fastapi import APIRouter

import app.service.external_url
from app.routers.admin import router as admin_router

ROUTE = "external-url"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)
read_one = router.get("/{id_}")(app.service.external_url.read_one)
read_many = router.get("")(app.service.external_url.read_many)
create_one = router.post("")(app.service.external_url.create_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.external_url.admin_read_one)
