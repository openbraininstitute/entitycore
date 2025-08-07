from fastapi import APIRouter

import app.service.circuit
import app.service.hierarchy

router = APIRouter(
    prefix="/circuit",
    tags=["circuit"],
)

hierarchy = router.get("/hierarchy")(app.service.hierarchy.read_circuit_hierarchy)
read_many = router.get("")(app.service.circuit.read_many)
read_one = router.get("/{id_}")(app.service.circuit.read_one)
create_one = router.post("")(app.service.circuit.create_one)
