from fastapi import APIRouter

import app.service.scientific_artifact_publication_link

router = APIRouter(
    prefix="/scientific-artifact-publication-link",
    tags=["scientific-artifact-publication-link"],
)

read_one = router.get("/{id_}")(app.service.scientific_artifact_publication_link.read_one)
read_many = router.get("")(app.service.scientific_artifact_publication_link.read_many)
create_one = router.post("")(app.service.scientific_artifact_publication_link.create_one)
