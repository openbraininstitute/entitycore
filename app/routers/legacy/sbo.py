from fastapi import APIRouter, HTTPException

from app.db.model import Entity
from app.dependencies.db import SessionDep
from app.routers.legacy.model import utils

router = APIRouter(
    prefix="/nexus/v1/search/query/suite",
    tags=["legacy_sbo"],
)


@router.post("/sbo")
def legacy_sbo(query: dict, db: SessionDep):
    try:
        db_type = utils.get_db_type(query)

        aggs = query.get("aggs")
        musts = utils.find_term_keys(query.get("query", {}))

        db_query = db.query(db_type)
        db_query = utils.add_predicates_to_query(db_query, musts, db_type)
        db_query_hits = db_query
        from_ = query.get("from")
        size = query.get("size")
        if from_ is not None:
            db_query_hits = db_query_hits.offset(from_)
        if size is not None:
            db_query_hits = db_query_hits.limit(size)
        hits = db_query_hits.all()
        count = db_query.count()
        if hits and db_type == Entity:
            # sometimes there is no type given
            # although it needs facets
            db_type = hits[0].__class__
        facets = utils.get_facets(aggs, musts, db_type, db)
        response = utils.build_response_body(facets=facets, hits=hits, count=count)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return response
