import app.service.circuit_extraction_execution as service
from app.routers.admin import router as admin_router
from app.routers.common import create_user_router, register_default_admin_routes
from app.routers.types import ActivityRoute

ROUTE = ActivityRoute.circuit_extraction_execution
router = create_user_router(route=ROUTE, service=service)
register_default_admin_routes(router=admin_router, service=service, route=ROUTE)
