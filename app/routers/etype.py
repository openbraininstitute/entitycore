from fastapi import APIRouter

import app.service.etype

router = APIRouter(
    prefix="/etype",
    tags=["etype"],
)

read_many = router.get("")(app.service.etype.read_many)
read_one = router.get("/{id_}")(app.service.etype.read_one)
delete_one = router.delete("/{id_}")(app.service.etype.delete_one)
