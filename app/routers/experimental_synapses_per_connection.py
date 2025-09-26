from fastapi import APIRouter

import app.service.experimental_synapses_per_connection
from app.routers.admin import router as admin_router

ROUTE = "experimental-synapses-per-connection"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.experimental_synapses_per_connection.read_many)
read_one = router.get("/{id_}")(app.service.experimental_synapses_per_connection.read_one)
create_one = router.post("")(app.service.experimental_synapses_per_connection.create_one)
update_one = router.patch("/{id_}")(app.service.experimental_synapses_per_connection.update_one)
delete_one = router.delete("/{id_}")(app.service.experimental_synapses_per_connection.delete_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.experimental_synapses_per_connection.admin_read_one
)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(
    app.service.experimental_synapses_per_connection.admin_update_one
)
