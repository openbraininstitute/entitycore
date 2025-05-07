from fastapi import APIRouter, Depends

import app.service.label
from app.dependencies.auth import user_with_service_admin_role

router = APIRouter(
    prefix="/label",
    tags=["label"],
)

read_many = router.get("")(app.service.label.read_many)
read_one = router.get("/{id_}")(app.service.label.read_one)
create_one = router.post("", dependencies=[Depends(user_with_service_admin_role)])(
    app.service.label.create_one
)
delete_one = router.delete("/{id_}", dependencies=[Depends(user_with_service_admin_role)])(
    app.service.label.delete_one
)
