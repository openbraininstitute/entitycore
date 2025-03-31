from fastapi import APIRouter, Depends

import app.service.role
from app.dependencies.auth import user_with_service_admin_role

router = APIRouter(
    prefix="/role",
    tags=["role"],
)

read_many = router.get("")(app.service.role.read_many)
read_one = router.get("/{id_}")(app.service.role.read_one)
create = router.post("", dependencies=[Depends(user_with_service_admin_role)])(
    app.service.role.create
)
