from fastapi import APIRouter

import app.service.memodel

router = APIRouter(
    prefix="/memodel",
    tags=["memodel"],
)

read_many = router.get("")(app.service.memodel.read_many)
read_one = router.get("/{id_}")(app.service.memodel.read_one)
create_one = router.post("")(app.service.memodel.create_one)
update_one = router.patch("/{id_}")(app.service.memodel.update_one)
