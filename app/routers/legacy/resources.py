from fastapi import APIRouter, Depends, HTTPException, Request
from app.models.base import Root
from urllib.parse import unquote
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.dependencies.db import get_db
from app.schemas.agent import PersonRead
import json
import os
router = APIRouter(
    prefix="/nexus/v1/resources",
    tags=["legacy_resources"],
)

def create_legacy_resource_body(db_element, extracted_url):
    ret = PersonRead.model_validate(db_element).dict()
    ret['@id'] = extracted_url
    return ret 



@router.get("/{path:path}")
def legacy_resources(path: str, db: Session = Depends(get_db)):
    # Extract the part after '_/'
    try:
        # Extract the portion of the URL that starts after the prefix
        prefix = "/nexus/v1/resources"

        # Locate the `_` and the portion after `_/`

        if "_/" in path:
            extracted_url = unquote(path.split("_/")[1])
            # Return the extracted URL or process it further
            print(extracted_url)
            if "ontologies/core/brainregion" in extracted_url:
                with open(os.path.join(os.path.dirname(__file__), "data/atlas_ontology.json"), "r") as f:
                    return json.load(f)
                return 
            use_func = func.instr
            if db.bind.dialect.name == "postgresql":
                use_func = func.strpos
            db_element = (
                db.query(Root)
                .filter(use_func(Root.legacy_id, extracted_url) > 0)
                .first()
            )
            print(db_element)
            return create_legacy_resource_body(db_element, extracted_url)
        else:
            return {"error": "'_/' not found in URL"}
    except Exception as e:
        return {"error": str(e)}
