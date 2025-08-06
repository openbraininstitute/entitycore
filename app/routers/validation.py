from fastapi import APIRouter

import app.service.validation

router = APIRouter(
    prefix="/validation",
    tags=["validation"],
)

read_many = router.get("")(app.service.validation.read_many)
read_one = router.get("/{id_}")(app.service.validation.read_one)
create_one = router.post("")(app.service.validation.create_one)
delete_one = router.delete("/{id_}")(app.service.validation.delete_one)
update_one = router.patch("/{id_}")(app.service.validation.update_one)
