from fastapi import APIRouter

import app.service.brain_region

router = APIRouter(
    prefix="/brain-region",
    tags=["brain-region"],
)

read_many = router.get("")(app.service.brain_region.read_many)
read_one = router.get("/{id_}")(app.service.brain_region.read_one)
