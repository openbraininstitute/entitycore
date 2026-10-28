# app/routers/task_result.py
import app.service.task_result as service
from app.routers.admin import router as admin_router
from app.routers.common import create_user_router, register_default_admin_routes
from app.types import EntityRoute

ROUTE = EntityRoute.task_result
router = create_user_router(route=ROUTE, service=service)
register_default_admin_routes(router=admin_router, service=service, route=ROUTE)
