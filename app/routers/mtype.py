from fastapi import APIRouter

import app.service.mtype

router = APIRouter(
    prefix="/mtype",
    tags=["mtype"],
)

read_many = router.get("")(app.service.mtype.read_many)
read_one = router.get("/{id_}")(app.service.mtype.read_one)
