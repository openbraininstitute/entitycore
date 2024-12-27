from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import app.models.density
import app.models.morphology
import app.models.single_cell_experimental_trace
from app.dependencies.db import get_db
from app.routers.legacy.model import utils

router = APIRouter(
    prefix="/nexus/v1/search/query/suite",
    tags=["legacy_sbo"],
)

MAP_KEYWORD = {
    "https://neuroshapes.org/ReconstructedNeuronMorphology": app.models.morphology.ReconstructionMorphology,
    "https://bbp.epfl.ch/ontologies/core/bmo/ExperimentalTrace": app.models.single_cell_experimental_trace.SingleCellExperimentalTrace,
    "https://bbp.epfl.ch/ontologies/core/bmo/ExperimentalNeuronDensity": app.models.density.ExperimentalNeuronDensity,
    "https://bbp.epfl.ch/ontologies/core/bmo/ExperimentalBoutonDensity": app.models.density.ExperimentalBoutonDensity,
    "https://bbp.epfl.ch/ontologies/core/bmo/ExperimentalSynapsesPerConnection": app.models.density.ExperimentalSynapsesPerConnection,
}


@router.post("/sbo")
def legacy_sbo(query: dict, db: Session = Depends(get_db)):
    terms = query.get("query", {}).get("bool", {}).get("must", [])
    if not terms:
        raise HTTPException(status_code=400, detail="No search terms provided")
    from_ = query.get("from", None)
    size = query.get("size", None)
    type_term = [term for term in terms if "@type.keyword" in term.get("term", {})]
    type_keyword = type_term[0].get("term", {}).get("@type.keyword", "")
    # br_terms = [
    #     term for term in terms if "brainRegion.@id.keyword" in term.get("terms", {})
    # ]
    db_type = MAP_KEYWORD.get(type_keyword)
    db_query = db.query(db_type)
    # if br_terms:
    #     regions = br_terms[0].get("terms", {}).get("brainRegion.@id.keyword", [])
    # if not size:
    #     if br_terms:
    #         db_query = (
    #             db_query.join(db_type.brain_region)
    #             .filter(base.BrainRegion.ontology_id.in_(regions))
    #             .distinct()
    #         )
    #     return utils.build_count_response_body(db_query.count())
    aggs = query.get("aggs", None)
    facets = utils.get_facets(aggs, db_type, db)
    db_query_hits = db_query
    if from_ is not None:
        db_query_hits = db_query_hits.offset(from_)
    if size is not None:
        db_query_hits = db_query_hits.limit(size)
    hits = db_query_hits.all()
    count = db_query.count()

    response = utils.build_response_body(facets=facets, hits=hits, count=count)

    return response
