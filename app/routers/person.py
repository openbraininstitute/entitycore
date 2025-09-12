from fastapi import APIRouter

import app.service.person
from app.routers.admin import router as admin_router

ROUTE = "person"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)


read_many = router.get("")(app.service.person.read_many)
read_one = router.get("/{id_}")(app.service.person.read_one)
create_one = router.post("")(app.service.person.create_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.person.admin_read_one)
