from fastapi import APIRouter

import app.service.external_data_source

router = APIRouter(
    prefix="/external-data-source",
    tags=["external-data-source"],
)
read_many = router.get("")(app.service.external_data_source.read_many)
read_one = router.get("/{id_}")(app.service.external_data_source.read_one)
create_one = router.post("")(app.service.external_data_source.create_one)
