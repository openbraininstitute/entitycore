from fastapi import APIRouter

import app.service.contribution
from app.routers.admin import router as admin_router

ROUTE = "contribution"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.contribution.read_many)
read_one = router.get("/{id_}")(app.service.contribution.read_one)
create_one = router.post("")(app.service.contribution.create_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.contribution.admin_read_one)
