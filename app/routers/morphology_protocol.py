from fastapi import APIRouter

import app.service.morphology_protocol

router = APIRouter(
    prefix="/morphology-protocol",
    tags=["morphology-protocol"],
)

read_many = router.get("")(app.service.morphology_protocol.read_many)
read_one = router.get("/{id_}")(app.service.morphology_protocol.read_one)
create_one = router.post("")(app.service.morphology_protocol.create_one)
