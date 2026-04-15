import app.service.brain_region_hierarchy as service
from app.routers.admin import router as admin_router
from app.routers.common import create_user_router, register_default_admin_routes
from app.routers.types import GlobalRoute

ROUTE = GlobalRoute.brain_region_hierarchy
router = create_user_router(
    route=ROUTE,
    service=service,
    after_routes=[
        lambda router: router.get("/{id_}/hierarchy")(service.read_hierarchy),
    ],
)
register_default_admin_routes(router=admin_router, service=service, route=ROUTE)
