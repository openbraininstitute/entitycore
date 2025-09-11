from fastapi import APIRouter

import app.service.validation_result

router = APIRouter(
    prefix="/validation-result",
    tags=["validation-result"],
)

read_many = router.get("")(app.service.validation_result.read_many)
read_one = router.get("/{id_}")(app.service.validation_result.read_one)
create_one = router.post("")(app.service.validation_result.create_one)
update_one = router.patch("/{id_}")(app.service.validation_result.update_one)
