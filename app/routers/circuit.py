import app.service.circuit as service
from app.routers.admin import router as admin_router
from app.routers.common import create_user_router, register_default_admin_routes
from app.routers.types import EntityRoute
from app.service.hierarchy import read_circuit_hierarchy

ROUTE = EntityRoute.circuit
router = create_user_router(route=ROUTE, service=service)
hierarchy = router.get("/hierarchy")(read_circuit_hierarchy)
register_default_admin_routes(router=admin_router, service=service, route=ROUTE)
