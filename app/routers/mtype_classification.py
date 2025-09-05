from fastapi import APIRouter

import app.service.mtype_classification

router = APIRouter(
    prefix="/mtype-classification",
    tags=["mtype-classification"],
)

create_one = router.post("")(app.service.mtype_classification.create_one)
read_one = router.get("/{id_}")(app.service.mtype_classification.read_one)
read_many = router.get("")(app.service.mtype_classification.read_many)
