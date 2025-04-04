import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.dependencies.db import SessionDep
from app.routers.legacy.model import class_ontology, utils

router = APIRouter(
    prefix="/nexus/v1/views",
    tags=["legacy_search"],
)


@router.post("/{path:path}/_search")
def legacy_search(query: dict, path: str, db: SessionDep):  # noqa: ARG001
    try:
        terms = query.get("query", {}).get("bool", {}).get("must", [])
        # if not terms:
        #     raise HTTPException(status_code=400, detail="No search terms provided")
        # type_term = [term for term in terms if "@type" in term.get("term", {})]
        # if not type_term:
        #     raise HTTPException(status_code=400, detail="No @type term provided")
        # type_term = type_term[0].get("term", {}).get("@type", "")
        # if not type_term:
        #     raise HTTPException(status_code=400, detail="empty @type provided")
        # if type_term == "License":
        #     return license.search(query, db)
        # if type_term == "Class":
        #     return class_ontology.search(query, db)
        # if type_term == "Mesh":
        #     return mesh.search(query, db)
        if terms:
            type_term = [term for term in terms if "@type" in term.get("term", {})]
            if type_term:
                type_term = type_term[0].get("term", {}).get("@type", "")
            if type_term == "Class":
                return class_ontology.search(query, db)
            if type_term == "GeneratorTaskActivity":
                with (
                    Path(__file__).parent / "search_data" / "GeneratorTaskActivity.json"
                ).open() as f:
                    return json.load(f)
        db_type = utils.get_db_type(query)
        musts = utils.find_term_keys(query.get("query", {}))
        db_query = db.query(db_type)
        db_query = utils.add_predicates_to_query(db_query, musts, db_type)
        from_ = query.get("from")
        size = query.get("size")
        if from_ is not None:
            db_query = db_query.offset(from_)
        if size is not None:
            db_query = db_query.limit(size)
        hits = db_query.all()
        count = db_query.count()
        response = utils.build_response_body(hits=hits, count=count)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return response
