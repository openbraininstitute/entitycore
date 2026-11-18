import app.service.em_dense_reconstruction_dataset as service
from app.routers.admin import router as admin_router
from app.routers.common import UserOperation, create_user_router, register_default_admin_routes
from app.types import EntityRoute

ROUTE = EntityRoute.em_dense_reconstruction_dataset
# the writes are reserved to admins, and available only through the admin routes
router = create_user_router(
    route=ROUTE,
    service=service,
    operations={UserOperation.read_many, UserOperation.read_one},
)
register_default_admin_routes(router=admin_router, service=service, route=ROUTE)
