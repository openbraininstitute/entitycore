import app.service.cell_morphology_protocol as service
from app.routers.admin import router as admin_router
from app.routers.common import create_user_router, register_default_admin_routes
from app.routers.types import EntityRoute

ROUTE = EntityRoute.cell_morphology_protocol
router = create_user_router(route=ROUTE, service=service)
register_default_admin_routes(router=admin_router, service=service, route=ROUTE)
