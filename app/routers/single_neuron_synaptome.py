from fastapi import APIRouter

import app.service.single_neuron_synaptome
from app.routers.admin import router as admin_router

ROUTE = "single-neuron-synaptome"
router = APIRouter(prefix=f"/{ROUTE}", tags=[ROUTE])

read_many = router.get("")(app.service.single_neuron_synaptome.read_many)
read_one = router.get("/{id_}")(app.service.single_neuron_synaptome.read_one)
create_one = router.post("")(app.service.single_neuron_synaptome.create_one)
update_one = router.patch("/{id_}")(app.service.single_neuron_synaptome.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.single_neuron_synaptome.admin_read_one
)
