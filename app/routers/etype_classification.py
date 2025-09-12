from fastapi import APIRouter

import app.service.etype_classification
from app.routers.admin import router as admin_router

ROUTE = "etype-classification"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

create_one = router.post("")(app.service.etype_classification.create_one)
read_one = router.get("/{id_}")(app.service.etype_classification.read_one)
read_many = router.get("")(app.service.etype_classification.read_many)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.etype_classification.admin_read_one
)
