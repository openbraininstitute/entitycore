from fastapi import APIRouter

import app.service.mtype_classification
from app.routers.admin import router as admin_router

ROUTE = "mtype-classification"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

create_one = router.post("")(app.service.mtype_classification.create_one)
read_one = router.get("/{id_}")(app.service.mtype_classification.read_one)
read_many = router.get("")(app.service.mtype_classification.read_many)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.mtype_classification.admin_read_one
)
