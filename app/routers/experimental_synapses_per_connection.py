from fastapi import APIRouter

import app.service.experimental_synapses_per_connection

router = APIRouter(
    prefix="/experimental-synapses-per-connection",
    tags=["experimental-synapses-per-connection"],
)

read_many = router.get("")(app.service.experimental_synapses_per_connection.read_many)
read_one = router.get("/{id_}")(app.service.experimental_synapses_per_connection.read_one)
create_one = router.post("")(app.service.experimental_synapses_per_connection.create_one)
