from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.routers.legacy.model import utils

router = APIRouter(
    prefix="/nexus/v1/search/query/suite",
    tags=["legacy_sbo"],
)


@router.post("/sbo")
def legacy_sbo(query: dict, db: Session = Depends(get_db)):
    db_type = utils.get_db_type(query)

    aggs = query.get("aggs", None)
    musts = query.get("query", {}).get("bool", {}).get("must", [])
    facets = utils.get_facets(aggs, musts, db_type, db)

    db_query = db.query(db_type)
    db_query = utils.add_predicates_to_query(db_query, musts, db_type)
    db_query_hits = db_query
    from_ = query.get("from", None)
    size = query.get("size", None)
    if from_ is not None:
        db_query_hits = db_query_hits.offset(from_)
    if size is not None:
        db_query_hits = db_query_hits.limit(size)
    hits = db_query_hits.all()
    count = db_query.count()

    response = utils.build_response_body(facets=facets, hits=hits, count=count)

    return response
