from fastapi import APIRouter

import app.service.etype_classification

router = APIRouter(
    prefix="/etype-classification",
    tags=["etype-classification"],
)

read_many = router.get("")(app.service.etype_classification.read_many)
read_one = router.get("/{id_}")(app.service.etype_classification.read_one)
create_one = router.post("")(app.service.etype_classification.create_one)
