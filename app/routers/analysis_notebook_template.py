from fastapi import APIRouter

import app.service.analysis_notebook_template as service
from app.routers.admin import router as admin_router
from app.routers.common import create_user_router, register_default_admin_routes
from app.types import EntityRoute

ROUTE = EntityRoute.analysis_notebook_template


def _add_clone_route(router: APIRouter) -> None:
    router.post("/{id_}/clone")(service.clone)


router = create_user_router(route=ROUTE, service=service, after_routes=[_add_clone_route])
register_default_admin_routes(router=admin_router, service=service, route=ROUTE)
