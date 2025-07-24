from fastapi import APIRouter

import app.service.external_database_url

router = APIRouter(
    prefix="/external-database-url",
    tags=["external-database-url"],
)
read_many = router.get("")(app.service.external_database_url.read_many)
read_one = router.get("/{id_}")(app.service.external_database_url.read_one)
create_one = router.post("")(app.service.external_database_url.create_one)
