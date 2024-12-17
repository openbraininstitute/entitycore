import app.routers.legacy.model.utils as utils
import app.models.annotation as annotation
def search(body, db):
    # for the time being only 1 query
    try:
        query_mtype = db.query(annotation.MTypeAnnotationBody)
        query_etype = db.query(annotation.ETypeAnnotationBody)
        result = query_mtype.all() + (query_etype).all()
        return utils.build_response_body(result)
    finally:
        db.close()