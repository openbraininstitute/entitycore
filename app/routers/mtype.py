from fastapi import APIRouter

import app.service.mtype
from app.routers.admin import router as admin_router

ROUTE = "mtype"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.mtype.read_many)
read_one = router.get("/{id_}")(app.service.mtype.read_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.mtype.read_one)
