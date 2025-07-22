from fastapi import APIRouter

import app.service.publication

router = APIRouter(
    prefix="/publication",
    tags=["publication"],
)

read_one = router.get("/{id_}")(app.service.publication.read_one)
read_many = router.get("")(app.service.publication.read_many)
create_one = router.post("")(app.service.publication.create_one)
