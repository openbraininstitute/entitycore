from app.db.model import ETypeClass
from app.routers.legacy.model import utils


def search(body, db):  # noqa: ARG001
    # for the time being only 1 query
    try:
        query_etype = db.query(ETypeClass)
        result = query_etype.all()
        return utils.build_response_body(hits=result, count=len(result))
    finally:
        db.close()
