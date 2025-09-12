from fastapi import APIRouter

import app.service.scientific_artifact_publication_link
from app.routers.admin import router as admin_router

ROUTE = "scientific-artifact-publication-link"

router = APIRouter(
    prefix=f"/{ROUTE}",
    tags=[ROUTE],
)

read_one = router.get("/{id_}")(app.service.scientific_artifact_publication_link.read_one)
read_many = router.get("")(app.service.scientific_artifact_publication_link.read_many)
create_one = router.post("")(app.service.scientific_artifact_publication_link.create_one)

admin_read_one = admin_router.get(f"/{ROUTE}/{{id_}}")(
    app.service.scientific_artifact_publication_link.admin_read_one
)
