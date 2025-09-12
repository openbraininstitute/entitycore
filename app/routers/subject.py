from fastapi import APIRouter

import app.service.subject
from app.routers.admin import router as admin_router

router = APIRouter(
    prefix="/subject",
    tags=["subject"],
)

read_many = router.get("")(app.service.subject.read_many)
read_one = router.get("/{id_}")(app.service.subject.read_one)
create_one = router.post("")(app.service.subject.create_one)
update_one = router.patch("/{id_}")(app.service.subject.update_one)

admin_update_one = admin_router.patch("/subject/{id_}")(app.service.subject.admin_update_one)
