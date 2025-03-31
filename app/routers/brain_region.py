from fastapi import APIRouter, Depends

import app.service.brain_region
from app.dependencies.auth import user_with_service_admin_role

router = APIRouter(
    prefix="/brain-region",
    tags=["brain-region"],
)

read_hierarchy = router.get("")(app.service.brain_region.read_hierarchy)
read_one = router.get("/{id_}")(app.service.brain_region.read_one)
create = router.post("", dependencies=[Depends(user_with_service_admin_role)])(
    app.service.brain_region.create
)
