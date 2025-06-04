from fastapi import APIRouter

import app.service.person

router = APIRouter(
    prefix="/person",
    tags=["person"],
)


read_many = router.get("")(app.service.person.read_many)
read_one = router.get("/{id_}")(app.service.person.read_one)
create_one = router.post("")(app.service.person.create_one)
