from fastapi import APIRouter

import app.service.cell_composition
from app.routers.admin import router as admin_router

ROUTE = "cell-composition"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_one = router.get("/{id_}")(app.service.cell_composition.read_one)
read_many = router.get("")(app.service.cell_composition.read_many)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(app.service.cell_composition.admin_read_one)
