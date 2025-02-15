from app.db.model import Mesh
from app.routers.legacy.model import utils


def build_mesh_elem(elem):
    return {
        "_id": elem.legacy_id[0],
        "_source": {
            "@id": elem.legacy_id[0],
            "@type": ["Mesh"],
            "brainLocation": {
                "brainRegion": {
                    "@id": elem.brain_region.ontology_id,
                }
            },
            "distribution": {
                "contentUrl": elem.content_url,
            },
        },
    }


def search(body, db):  # noqa: ARG001
    try:
        query = db.query(Mesh)
        hits = query.all()
        count = len(hits)
        return utils.build_response_body(hits=hits, count=count, build_func=build_mesh_elem)
    finally:
        db.close()
