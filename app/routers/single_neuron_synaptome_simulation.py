from fastapi import APIRouter

import app.service.single_neuron_synaptome_simulation

router = APIRouter(
    prefix="/single-neuron-synaptome-simulation",
    tags=["single-neuron-synaptome-simulation"],
)

read_many = router.get("")(app.service.single_neuron_synaptome_simulation.read_many)
read_one = router.get("/{id_}")(app.service.single_neuron_synaptome_simulation.read_one)
create_one = router.post("")(app.service.single_neuron_synaptome_simulation.create_one)
