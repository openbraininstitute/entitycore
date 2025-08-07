from fastapi import APIRouter

import app.service.simulation_campaign

router = APIRouter(
    prefix="/simulation-campaign",
    tags=["simulation-campaign"],
)

read_many = router.get("")(app.service.simulation_campaign.read_many)
read_one = router.get("/{id_}")(app.service.simulation_campaign.read_one)
create_one = router.post("")(app.service.simulation_campaign.create_one)
