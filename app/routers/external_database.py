from fastapi import APIRouter

import app.service.external_database

router = APIRouter(
    prefix="/external-database",
    tags=["external-database"],
)
read_many = router.get("")(app.service.external_database.read_many)
read_one = router.get("/{id_}")(app.service.external_database.read_one)
create_one = router.post("")(app.service.external_database.create_one)
