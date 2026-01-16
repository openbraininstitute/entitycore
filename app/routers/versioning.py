"""Generic versioning routes."""

from fastapi.routing import APIRouter

from app.service import versioning as service

router = APIRouter(
    prefix="",
    tags=["version"],
)

router.get("/{resource_route}/{resource_id}/version-count")(service.get_version_count)
router.get("/{resource_route}/{resource_id}/version/{version_num}")(service.get_version_model)
router.get("/{resource_route}/{resource_id}/version/{version_num}/changeset")(
    service.get_version_changeset
)
