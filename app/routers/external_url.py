from fastapi import APIRouter

import app.service.external_url

router = APIRouter(
    prefix="/external-url",
    tags=["external-url"],
)
read_many = router.get("")(app.service.external_url.read_many)
read_one = router.get("/{id_}")(app.service.external_url.read_one)
create_one = router.post("")(app.service.external_url.create_one)
