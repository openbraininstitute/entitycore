from fastapi import APIRouter

import app.service.simulation_generation

router = APIRouter(
    prefix="/simulation-generation",
    tags=["simulation-generation"],
)

read_many = router.get("")(app.service.simulation_generation.read_many)
read_one = router.get("/{id_}")(app.service.simulation_generation.read_one)
create_one = router.post("")(app.service.simulation_generation.create_one)
delete_one = router.delete("/{id_}")(app.service.simulation_generation.delete_one)
