from fastapi import APIRouter

import app.service.morphology_feature_annotation

router = APIRouter(
    prefix="/morphology-feature-annotation",
    tags=["morphology-feature-annotation"],
)

read_many = router.get("")(app.service.morphology_feature_annotation.read_many)
read_one = router.get("/{id_}")(app.service.morphology_feature_annotation.read_one)
create = router.post("")(app.service.morphology_feature_annotation.create)
