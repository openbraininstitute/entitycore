
from fastapi import APIRouter, Depends, HTTPException
from app.routers.legacy.model import license, class_ontology

from sqlalchemy.orm import Session
from app.dependencies.db import get_db
router = APIRouter(
    prefix='/nexus/v1/views/bbp/atlas/https://bbp.epfl.ch/data/bbp/atlas/es_aggregate_view_tags_v1.1.0_v2.2.4',
    tags=["legacy_search"],
)

@router.post("/_search")
def legacy_search(query: dict, db: Session = Depends(get_db)):
    terms = query.get("query", {}).get("bool", {}).get("must", [])
    if not terms:
        raise HTTPException(status_code=400, detail="No search terms provided")
    type_term = [term for term in terms if "@type" in term.get("term", {})]
    if not type_term:
        raise HTTPException(status_code=400, detail="No @type term provided")
    type_term = type_term[0].get("term", {}).get("@type", "")
    if not type_term:
        raise HTTPException(status_code=400, detail="empty @type provided")
    if type_term == "License":
        return license.search(query, db)
    if type_term == "Class":
        return class_ontology.search(query, db)
    assert False, "unreachable"