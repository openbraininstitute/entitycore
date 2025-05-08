from fastapi import APIRouter

import app.service.measurement_annotation

router = APIRouter(
    prefix="/measurement-annotation",
    tags=["measurement-annotation"],
)

read_many = router.get("")(app.service.measurement_annotation.read_many)
read_one = router.get("/{id_}")(app.service.measurement_annotation.read_one)
create_one = router.post("")(app.service.measurement_annotation.create_one)
delete_one = router.delete("/{id_}")(app.service.measurement_annotation.delete_one)
