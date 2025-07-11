from fastapi import APIRouter

import app.service.single_neuron_synaptome

router = APIRouter(
    prefix="/single-neuron-synaptome",
    tags=["single-neuron-synaptome"],
)

read_many = router.get("")(app.service.single_neuron_synaptome.read_many)
read_one = router.get("/{id_}")(app.service.single_neuron_synaptome.read_one)
create_one = router.post("")(app.service.single_neuron_synaptome.create_one)
delete_one = router.delete("/{id_}")(app.service.single_neuron_synaptome.delete_one)
