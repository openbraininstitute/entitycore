import app.service.brain_atlas as service
from app.routers.admin import router as admin_router
from app.routers.common import create_user_router, register_default_admin_routes
from app.schemas.brain_atlas_region import BrainAtlasRegionRead
from app.schemas.types import ListResponse
from app.types import EntityRoute
from app.utils.http_cache import NOT_MODIFIED_RESPONSE

ROUTE = EntityRoute.brain_atlas
router = create_user_router(
    route=ROUTE,
    service=service,
    after_routes=[
        lambda router: router.get(
            "/{atlas_id}/regions",
            response_model=ListResponse[BrainAtlasRegionRead],
            responses=NOT_MODIFIED_RESPONSE,
        )(service.read_many_region),
        lambda router: router.get("/{atlas_id}/regions/{atlas_region_id}")(service.read_one_region),
    ],
)
register_default_admin_routes(router=admin_router, service=service, route=ROUTE)
