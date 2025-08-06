from fastapi import APIRouter

import app.service.hierarchy

router = APIRouter(
    prefix="/hierarchy",
    tags=["hierarchy"],
)

router.get("/circuit")(app.service.hierarchy.read_circuit_hierarchy)
