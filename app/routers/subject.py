from fastapi import APIRouter

import app.service.subject
from app.routers.admin import router as admin_router

ROUTE = "subject"
router = APIRouter(prefix=f"/{ROUTE}", tags=[ROUTE])

read_many = router.get("")(app.service.subject.read_many)
read_one = router.get("/{id_}")(app.service.subject.read_one)
create_one = router.post("")(app.service.subject.create_one)
update_one = router.patch("/{id_}")(app.service.subject.update_one)
delete_one = router.delete("/{id_}")(app.service.subject.delete_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.subject.admin_read_one)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(app.service.subject.admin_update_one)
