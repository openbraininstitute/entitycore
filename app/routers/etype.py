from fastapi import APIRouter

import app.service.etype
from app.routers.admin import router as admin_router

ROUTE = "etype"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.etype.read_many)
read_one = router.get("/{id_}")(app.service.etype.read_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.etype.read_one)
