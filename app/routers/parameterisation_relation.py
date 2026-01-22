from fastapi import APIRouter

import app.service.parameterisation_relation
from app.routers.admin import router as admin_router

ROUTE = "parameterisation-relation"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_many = router.get("")(app.service.parameterisation_relation.read_many)
read_one = router.get("/{id_}")(app.service.parameterisation_relation.read_one)
create_one = router.post("")(app.service.parameterisation_relation.create_one)
update_one = router.patch("/{id_}")(app.service.parameterisation_relation.update_one)
delete_one = router.delete("/{id_}")(app.service.parameterisation_relation.delete_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.parameterisation_relation.admin_read_one
)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(
    app.service.parameterisation_relation.admin_update_one
)
