from fastapi import APIRouter, Depends

import app.service.license
from app.dependencies.auth import user_with_service_admin_role

router = APIRouter(
    prefix="/license",
    tags=["license"],
)

read_many = router.get("")(app.service.license.read_many)
read_one = router.get("/{id_}")(app.service.license.read_one)
create = router.post("", dependencies=[Depends(user_with_service_admin_role)])(
    app.service.license.create
)
