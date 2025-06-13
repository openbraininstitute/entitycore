from fastapi import APIRouter

import app.service.simulation_execution

router = APIRouter(
    prefix="/simulation-execution",
    tags=["simulation-execution"],
)

read_many = router.get("")(app.service.simulation_execution.read_many)
read_one = router.get("/{id_}")(app.service.simulation_execution.read_one)
create_one = router.post("")(app.service.simulation_execution.create_one)
