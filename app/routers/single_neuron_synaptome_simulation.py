from fastapi import APIRouter

import app.service.single_neuron_synaptome_simulation
from app.routers.admin import router as admin_router

ROUTE = "single-neuron-synaptome-simulation"
router = APIRouter(prefix=f"/{ROUTE}", tags=[ROUTE])

read_many = router.get("")(app.service.single_neuron_synaptome_simulation.read_many)
read_one = router.get("/{id_}")(app.service.single_neuron_synaptome_simulation.read_one)
create_one = router.post("")(app.service.single_neuron_synaptome_simulation.create_one)
update_one = router.patch("/{id_}")(app.service.single_neuron_synaptome_simulation.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.single_neuron_synaptome_simulation.admin_read_one
)
