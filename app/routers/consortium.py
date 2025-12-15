from fastapi import APIRouter

import app.service.consortium
from app.routers.admin import router as admin_router

ROUTE = "consortium"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.consortium.read_many)
read_one = router.get("/{id_}")(app.service.consortium.read_one)
create_one = router.post("")(app.service.consortium.create_one)
delete_one = router.delete("/{id_}")(app.service.consortium.delete_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.consortium.admin_read_one)
