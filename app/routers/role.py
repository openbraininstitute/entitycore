from fastapi import APIRouter

import app.service.role

router = APIRouter(
    prefix="/role",
    tags=["role"],
)

read_many = router.get("")(app.service.role.read_many)
read_one = router.get("/{id_}")(app.service.role.read_one)
create_one = router.post("")(app.service.role.create_one)
delete_one = router.delete("/{id_}")(app.service.role.delete_one)
