from fastapi import APIRouter

import app.service.single_neuron_simulation

router = APIRouter(
    prefix="/single-neuron-simulation",
    tags=["single-neuron-simulation"],
)

read_many = router.get("")(app.service.single_neuron_simulation.read_many)
read_one = router.get("/{id_}")(app.service.single_neuron_simulation.read_one)
create_one = router.post("")(app.service.single_neuron_simulation.create_one)
delete_one = router.delete("/{id_}")(app.service.single_neuron_simulation.delete_one)
