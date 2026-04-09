import app.service.brain_atlas as service
from app.routers.admin import router as admin_router
from app.routers.common import create_user_router, register_default_admin_routes
from app.routers.types import EntityRoute

ROUTE = EntityRoute.brain_atlas
router = create_user_router(route=ROUTE, service=service)
read_many_region = router.get("/{atlas_id}/regions")(service.read_many_region)
read_one_region = router.get("/{atlas_id}/regions/{atlas_region_id}")(service.read_one_region)
register_default_admin_routes(router=admin_router, service=service, route=ROUTE)
