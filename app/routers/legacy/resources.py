import json
import os
from urllib.parse import unquote

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.db.model import Root
from app.schemas.agent import PersonRead
from fastapi import HTTPException

router = APIRouter(
    prefix="/nexus/v1/resources",
    tags=["legacy_resources"],
)


def create_legacy_resource_body(db_element, extracted_url):
    ret = PersonRead.model_validate(db_element).dict()
    ret["@id"] = extracted_url
    return ret


RESOURCE_MAP = {
    "https://bbp.epfl.ch/neurosciencegraph/data/cellcompositions/54818e46-cf8c-4bd6-9b68-34dffbc8a68c": "CellComposition.json",
    "https://bbp.epfl.ch/data/bbp/mmb-point-neuron-framework-model/d28580b8-9fc8-4b04-8e67-11229b31726c": "ModelBuildingConfig.json",
    "https://bbp.epfl.ch/data/bbp/mmb-point-neuron-framework-model/f5c150ac-2678-4ae5-ae22-c5b43cad1906": "CellCompositionConfig.json",
    "https://bbp.epfl.ch/data/bbp/atlasdatasetrelease/ccc3a6c5-9f77-4917-bc2e-fc8d3879042c": "CellCompositionSummary.json",
    "https://bbp.epfl.ch/data/bbp/mmb-point-neuron-framework-model/2b29d249-6520-4a98-9586-27ec7803aed2": "DetailedCircuit.json",
}


@router.get("/{path:path}")
def legacy_resources(path: str, db: Session = Depends(get_db)):
    # Extract the part after '_/'
    try:
        # Locate the `_` and the portion after `_/`

        if "_/" in path:
            extracted_url = unquote(path.split("_/")[1])
            # Return the extracted URL or process it further
            if "ontologies/core/brainregion" in extracted_url:
                with open(
                    os.path.join(
                        os.path.dirname(__file__), "resources_data/atlas_ontology.json"
                    ),
                ) as f:
                    return json.load(f)
                return None
            if extracted_url in RESOURCE_MAP:
                with open(
                    os.path.join(
                        os.path.dirname(__file__),
                        "resources_data",
                        RESOURCE_MAP[extracted_url],
                    ),
                ) as f:
                    return json.load(f)
            db_element = (
                db.query(Root)
                .filter(func.strpos(Root.legacy_id, extracted_url) > 0)
                .first()
            )
            if not db_element:
                return HTTPException(status_code=404, detail="Resource not found")
            return create_legacy_resource_body(db_element, extracted_url)
        return {"error": "'_/' not found in URL"}
    except Exception as e:
        return {"error": str(e)}
