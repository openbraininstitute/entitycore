from fastapi import APIRouter

import app.service.organization

router = APIRouter(
    prefix="/organization",
    tags=["organization"],
)

read_many = router.get("")(app.service.organization.read_many)
read_one = router.get("/{id_}")(app.service.organization.read_one)
create_one = router.post("")(app.service.organization.create_one)
delete_one = router.delete("/{id_}")(app.service.organization.delete_one)
