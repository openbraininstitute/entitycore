from fastapi import APIRouter

import app.service.species

router = APIRouter(
    prefix="/species",
    tags=["species"],
)

read_many = router.get("")(app.service.species.read_many)
read_one = router.get("/{id_}")(app.service.species.read_one)
create_one = router.post("")(app.service.species.create_one)
