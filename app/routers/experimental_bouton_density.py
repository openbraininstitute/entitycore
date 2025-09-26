from fastapi import APIRouter

import app.service.experimental_bouton_density
from app.routers.admin import router as admin_router

ROUTE = "experimental-bouton-density"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.experimental_bouton_density.read_many)
read_one = router.get("/{id_}")(app.service.experimental_bouton_density.read_one)
create_one = router.post("")(app.service.experimental_bouton_density.create_one)
update_one = router.patch("/{id_}")(app.service.experimental_bouton_density.update_one)
delete_one = router.delete("/{id_}")(app.service.experimental_bouton_density.delete_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.experimental_bouton_density.admin_read_one
)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(
    app.service.experimental_bouton_density.admin_update_one
)
