import app.models.mesh as mesh
import app.routers.legacy.model.utils as utils


def build_mesh_elem(elem):
    return {
        "_id": elem.legacy_id[0],
        "_source": {
            "@id": elem.legacy_id[0],
            "@type": ["Mesh"],
            "brainLocation": {
                "brainRegion": {
                    '@id':elem.brain_region.ontology_id,
                }
            },
            "distribution": {
                "contentUrl": elem.content_url,
            },
        },
    }


def search(body, db):
    try:
        query = db.query(mesh.Mesh)
        return utils.build_response_body(query.all(), build_mesh_elem)
    finally:
        db.close()
