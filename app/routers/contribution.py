from fastapi import APIRouter

import app.service.contribution

router = APIRouter(
    prefix="/contribution",
    tags=["contribution"],
)

read_many = router.get("")(app.service.contribution.read_many)
read_one = router.get("/{id_}")(app.service.contribution.read_one)
create_one = router.post("")(app.service.contribution.create_one)
delete_one = router.delete("/{id_}")(app.service.contribution.delete_one)
