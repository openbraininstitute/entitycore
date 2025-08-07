from fastapi import APIRouter

import app.service.consortium

router = APIRouter(
    prefix="/consortium",
    tags=["consortium"],
)

read_many = router.get("")(app.service.consortium.read_many)
read_one = router.get("/{id_}")(app.service.consortium.read_one)
create_one = router.post("")(app.service.consortium.create_one)
