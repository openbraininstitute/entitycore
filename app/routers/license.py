from fastapi import APIRouter

import app.service.license

router = APIRouter(
    prefix="/license",
    tags=["license"],
)

read_many = router.get("")(app.service.license.read_many)
read_one = router.get("/{id_}")(app.service.license.read_one)
create_one = router.post("")(app.service.license.create_one)
