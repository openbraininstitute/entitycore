from fastapi import APIRouter

import app.service.external_url

router = APIRouter(
    prefix="/external-url",
    tags=["external-url"],
)
read_one = router.get("/{id_}")(app.service.external_url.read_one)
read_many = router.get("")(app.service.external_url.read_many)
create_one = router.post("")(app.service.external_url.create_one)
