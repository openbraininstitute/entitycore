from fastapi import APIRouter, Depends, HTTPException
from app.routers.legacy.model import license

from sqlalchemy.orm import Session
from app.dependencies.db import get_db
router = APIRouter(
    prefix='/nexus/v1/search/query/suite',
    tags=["legacy_sbo"],
)

@router.post("/sbo")
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
    assert type_term in ["neuronMorphology.@id.keyword"]
    # if type_term == "License":
    #     return license.search(query, db) 