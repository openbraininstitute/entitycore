from fastapi import APIRouter

import app.service.scientific_artifact_external_url_link

router = APIRouter(
    prefix="/scientific-artifact-external-url-link",
    tags=["scientific-artifact-external-url-link"],
)

read_one = router.get("/{id_}")(app.service.scientific_artifact_external_url_link.read_one)
read_many = router.get("")(app.service.scientific_artifact_external_url_link.read_many)
create_one = router.post("")(app.service.scientific_artifact_external_url_link.create_one)
