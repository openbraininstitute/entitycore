from fastapi import APIRouter

import app.service.etype_classification

router = APIRouter(
    prefix="/etype-classification",
    tags=["etype-classification"],
)

create_one = router.post("")(app.service.etype_classification.create_one)
read_one = router.get("/{id_}")(app.service.etype_classification.read_one)
read_many = router.get("")(app.service.etype_classification.read_many)
