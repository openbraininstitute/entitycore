from fastapi import APIRouter

import app.service.external_data_source_page

router = APIRouter(
    prefix="/external-data-source-page",
    tags=["external-data-source-page"],
)
read_many = router.get("")(app.service.external_data_source_page.read_many)
read_one = router.get("/{id_}")(app.service.external_data_source_page.read_one)
create_one = router.post("")(app.service.external_data_source_page.create_one)
