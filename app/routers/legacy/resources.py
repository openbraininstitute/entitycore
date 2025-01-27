import json
from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException
from sqlalchemy import func

from app.db.model import Root
from app.dependencies.db import SessionDep
from app.schemas.agent import PersonRead

router = APIRouter(
    prefix="/nexus/v1/resources",
    tags=["legacy_resources"],
)


def create_legacy_resource_body(db_element, extracted_url):
    ret = PersonRead.model_validate(db_element).dict()
    ret["@id"] = extracted_url
    return ret


RESOURCE_MAP = {
    "https://bbp.epfl.ch/neurosciencegraph/data/cellcompositions/54818e46-cf8c-4bd6-9b68-34dffbc8a68c": "CellComposition.json",  # noqa: E501
    "https://bbp.epfl.ch/data/bbp/mmb-point-neuron-framework-model/d28580b8-9fc8-4b04-8e67-11229b31726c": "ModelBuildingConfig.json",  # noqa: E501
    "https://bbp.epfl.ch/data/bbp/mmb-point-neuron-framework-model/f5c150ac-2678-4ae5-ae22-c5b43cad1906": "CellCompositionConfig.json",  # noqa: E501
    "https://bbp.epfl.ch/data/bbp/atlasdatasetrelease/ccc3a6c5-9f77-4917-bc2e-fc8d3879042c": "CellCompositionSummary.json",  # noqa: E501
    "https://bbp.epfl.ch/data/bbp/mmb-point-neuron-framework-model/2b29d249-6520-4a98-9586-27ec7803aed2": "DetailedCircuit.json",  # noqa: E501
}


@router.get("/{path:path}")
def legacy_resources(path: str, db: SessionDep):
    # Extract the part after '_/'
    try:
        # Locate the `_` and the portion after `_/`

        if "_/" not in path:
            return {"error": "'_/' not found in URL"}
        extracted_url = unquote(path.split("_/")[1])
        # Return the extracted URL or process it further
        if "ontologies/core/brainregion" in extracted_url:
            with (Path(__file__).parent / "resources_data" / "atlas_ontology.json").open() as f:
                return json.load(f)
        if extracted_url in RESOURCE_MAP:
            with (
                Path(__file__).parent / "resources_data" / RESOURCE_MAP[extracted_url]
            ).open() as f:
                return json.load(f)
        db_element = db.query(Root).filter(func.strpos(Root.legacy_id, extracted_url) > 0).first()
        if not db_element:
            return HTTPException(status_code=404, detail="Resource not found")
        return create_legacy_resource_body(db_element, extracted_url)
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}
