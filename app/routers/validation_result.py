from fastapi import APIRouter

import app.service.validation_result
from app.routers.admin import router as admin_router

ROUTE = "validation-result"
router = APIRouter(prefix=f"/{ROUTE}", tags=[ROUTE])

read_many = router.get("")(app.service.validation_result.read_many)
read_one = router.get("/{id_}")(app.service.validation_result.read_one)
create_one = router.post("")(app.service.validation_result.create_one)
update_one = router.patch("/{id_}")(app.service.validation_result.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.validation_result.admin_read_one)
