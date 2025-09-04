from fastapi import APIRouter

import app.service.experimental_neuron_density

router = APIRouter(
    prefix="/experimental-neuron-density",
    tags=["experimental-neuron-density"],
)

read_many = router.get("")(app.service.experimental_neuron_density.read_many)
read_one = router.get("/{id_}")(app.service.experimental_neuron_density.read_one)
create_one = router.post("")(app.service.experimental_neuron_density.create_one)
update_one = router.patch("/{id_}")(app.service.experimental_neuron_density.update_one)
