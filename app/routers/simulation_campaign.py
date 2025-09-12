from fastapi import APIRouter

import app.service.simulation_campaign
from app.routers.admin import router as admin_router

router = APIRouter(
    prefix="/simulation-campaign",
    tags=["simulation-campaign"],
)

read_many = router.get("")(app.service.simulation_campaign.read_many)
read_one = router.get("/{id_}")(app.service.simulation_campaign.read_one)
create_one = router.post("")(app.service.simulation_campaign.create_one)
update_one = router.patch("/{id_}")(app.service.simulation_campaign.update_one)

admin_update_one = admin_router.patch("/simulation-campaign/{id_}")(
    app.service.simulation_campaign.admin_update_one
)
