from fastapi import APIRouter, Depends

import app.service.species
from app.dependencies.auth import user_with_service_admin_role

router = APIRouter(
    prefix="/species",
    tags=["species"],
)

read_many = router.get("")(app.service.species.read_many)
read_one = router.get("/{id_}")(app.service.species.read_one)
create_one = router.post("", dependencies=[Depends(user_with_service_admin_role)])(
    app.service.species.create_one
)
