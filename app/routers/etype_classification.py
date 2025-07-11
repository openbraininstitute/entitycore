from fastapi import APIRouter

import app.service.etype_classification

router = APIRouter(
    prefix="/etype-classification",
    tags=["etype-classification"],
)

create_one = router.post("")(app.service.etype_classification.create_one)
delete_one = router.delete("/{id_}")(app.service.etype_classification.delete_one)
