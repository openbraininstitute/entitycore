from fastapi import APIRouter

import app.service.validation
from app.routers.admin import router as admin_router

ROUTE = "validation"
router = APIRouter(prefix=f"/{ROUTE}", tags=[ROUTE])

read_many = router.get("")(app.service.validation.read_many)
read_one = router.get("/{id_}")(app.service.validation.read_one)
create_one = router.post("")(app.service.validation.create_one)
delete_one = router.delete("/{id_}")(app.service.validation.delete_one)
update_one = router.patch("/{id_}")(app.service.validation.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.validation.admin_read_one)
