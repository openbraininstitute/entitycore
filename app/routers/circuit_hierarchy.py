from fastapi import APIRouter

import app.service.circuit_hierarchy

router = APIRouter(
    prefix="/circuit-hierarchy",
    tags=["circuit-hierarchy"],
)

read_structure = router.get("")(app.service.circuit_hierarchy.read_structure)
