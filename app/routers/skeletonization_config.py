from fastapi import APIRouter

from app.routers.admin import router as admin_router
from app.service import skeletonization_config as service

ROUTE = "skeletonization-config"
router = APIRouter(prefix=f"/{ROUTE}", tags=[ROUTE])

read_many = router.get("")(service.read_many)
read_one = router.get("/{id_}")(service.read_one)
create_one = router.post("")(service.create_one)
update_one = router.patch("/{id_}")(service.update_one)
delete_one = router.delete("/{id_}")(service.delete_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(service.admin_read_one)
admin_update_one = admin_router.patch(f"/{ROUTE}/{{id_}}")(service.admin_update_one)
