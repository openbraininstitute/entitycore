from fastapi import APIRouter

import app.service.simulation_result

router = APIRouter(
    prefix="/simulation-result",
    tags=["simulation-result"],
)

read_many = router.get("")(app.service.simulation_result.read_many)
read_one = router.get("/{id_}")(app.service.simulation_result.read_one)
create_one = router.post("")(app.service.simulation_result.create_one)
