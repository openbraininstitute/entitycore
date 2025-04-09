from fastapi import APIRouter, Depends

import app.service.strain
from app.dependencies.auth import user_with_service_admin_role

router = APIRouter(
    prefix="/strain",
    tags=["strain"],
)

read_many = router.get("")(app.service.strain.read_many)
read_one = router.get("/{id_}")(app.service.strain.read_one)
create_one = router.post("", dependencies=[Depends(user_with_service_admin_role)])(
    app.service.strain.create_one
)
