from app.models import annotation
from app.routers.legacy.model import utils


def search(body, db):
    # for the time being only 1 query
    try:
        query_mtype = db.query(annotation.MTypeAnnotationBody)
        query_etype = db.query(annotation.ETypeAnnotationBody)
        result = query_mtype.all() + (query_etype).all()
        return utils.build_response_body(hits=result, count=len(result))
    finally:
        db.close()
