from fastapi import APIRouter

import app.service.simulation

router = APIRouter(
    prefix="/simulation",
    tags=["simulation"],
)

read_many = router.get("")(app.service.simulation.read_many)
read_one = router.get("/{id_}")(app.service.simulation.read_one)
create_one = router.post("")(app.service.simulation.create_one)
update_one = router.patch("/{id_}")(app.service.simulation.update_one)
