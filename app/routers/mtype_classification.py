from fastapi import APIRouter

import app.service.mtype_classification

router = APIRouter(
    prefix="/mtype-classification",
    tags=["mtype-classification"],
)

create_one = router.post("")(app.service.mtype_classification.create_one)
