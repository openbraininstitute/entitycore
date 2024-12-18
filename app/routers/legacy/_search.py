from fastapi import APIRouter, Depends, HTTPException
from app.routers.legacy.model import license, class_ontology, mesh

from sqlalchemy.orm import Session
from app.dependencies.db import get_db
import os
import json

router = APIRouter(
    prefix="/nexus/v1/views",
    tags=["legacy_search"],
)


@router.post("/{path:path}/_search")
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
    if type_term == "Mesh":
        return mesh.search(query, db)
    if type_term == "GeneratorTaskActivity":
        with open(os.path.join(os.path.dirname(__file__), "search_data/GeneratorTaskActivity.json"), "r") as f:
            return json.load(f)
    assert False, "unreachable"
