from fastapi import APIRouter, Depends

import app.service.organization
from app.dependencies.auth import user_with_service_admin_role

router = APIRouter(
    prefix="/organization",
    tags=["organization"],
)

read_many = router.get("")(app.service.organization.read_many)
read_one = router.get("/{id_}")(app.service.organization.read_one)
create = router.post("", dependencies=[Depends(user_with_service_admin_role)])(
    app.service.organization.create
)
