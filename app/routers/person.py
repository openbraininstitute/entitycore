from fastapi import APIRouter, Depends

import app.service.person
from app.dependencies.auth import user_with_service_admin_role

router = APIRouter(
    prefix="/person",
    tags=["person"],
)


read_many = router.get("")(app.service.person.read_many)
read_one = router.get("/{id_}")(app.service.person.read_one)
create_one = router.post("", dependencies=[Depends(user_with_service_admin_role)])(
    app.service.person.create_one
)
