from fastapi import APIRouter

import app.service.circuit

router = APIRouter(
    prefix="/circuit",
    tags=["circuit"],
)

read_many = router.get("")(app.service.circuit.read_many)
read_one = router.get("/{id_}")(app.service.circuit.read_one)
create_one = router.post("")(app.service.circuit.create_one)
