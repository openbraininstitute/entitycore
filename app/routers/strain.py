from fastapi import APIRouter

import app.service.strain

router = APIRouter(
    prefix="/strain",
    tags=["strain"],
)

read_many = router.get("")(app.service.strain.read_many)
read_one = router.get("/{id_}")(app.service.strain.read_one)
create_one = router.post("")(app.service.strain.create_one)
delete_one = router.delete("/{id_}")(app.service.strain.delete_one)
