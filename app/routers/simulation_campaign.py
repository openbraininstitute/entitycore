from fastapi import APIRouter

import app.service.simulation_campaign
from app.routers.admin import router as admin_router

ROUTE = "simulation-campaign"
router = APIRouter(prefix=f"/{ROUTE}", tags=[ROUTE])

read_many = router.get("")(app.service.simulation_campaign.read_many)
read_one = router.get("/{id_}")(app.service.simulation_campaign.read_one)
create_one = router.post("")(app.service.simulation_campaign.create_one)
update_one = router.patch("/{id_}")(app.service.simulation_campaign.update_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.simulation_campaign.admin_read_one
)
