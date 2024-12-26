from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

import app.models.density
import app.models.morphology
import app.models.single_cell_experimental_trace
from app.dependencies.db import get_db
from app.models import agent, annotation, base, contribution, morphology
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
    br_terms = [
        term for term in terms if "brainRegion.@id.keyword" in term.get("terms", {})
    ]
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
    facets = {}
    if aggs is not None:
        QUERY_MAP = {
            morphology.ReconstructionMorphology: {
                "mType.label.keyword": {
                    "group_name": "pref_label",
                    "table": annotation.MTypeAnnotationBody,
                    "joins": [
                        {
                            "join": ("id", "annotation_body_id"),
                            "table": annotation.Annotation,
                        },
                        {
                            "join": ("entity_id", "id"),
                            "table": morphology.ReconstructionMorphology,
                        },
                    ],
                },
                "subjectSpecies.label.keyword": {
                    "group_name": "name",
                    "table": base.Species,
                    "joins": [
                        {
                            "join": ("id", "species_id"),
                            "table": morphology.ReconstructionMorphology,
                        }
                    ],
                },
                "contributors.label.keyword": {
                    "group_name": "familyName",
                    "table": agent.Person,
                    "joins": [
                        {
                            "join": ("id", "agent_id"),
                            "table": contribution.Contribution,
                        },
                        {
                            "join": ("entity_id", "id"),
                            "table": morphology.ReconstructionMorphology,
                        },
                    ],
                },
            }
        }
        fields = [
            {"label": key, "field": aggs[key]["terms"]["field"]} for key in aggs.keys()
        ]
        query_map = QUERY_MAP.get(db_type)
        for ty in fields:
            field_query_map = query_map.get(ty["field"])
            group_name = field_query_map["group_name"]
            table = field_query_map["table"]
            initial_alias = aliased(table)
            cur_alias = initial_alias
            facet_q = db.query(
                getattr(cur_alias, group_name), func.count().label("count")
            )
            for join in field_query_map["joins"]:
                prev_alias = cur_alias
                cur_alias = aliased(join["table"])
                facet_q = facet_q.join(
                    cur_alias,
                    getattr(prev_alias, join["join"][0])
                    == getattr(cur_alias, join["join"][1]),
                )
            facet_q = facet_q.group_by(getattr(initial_alias, group_name))
            facet_q = facet_q.order_by(func.count().desc())
            facets[ty["label"]] = facet_q.all()

    db_query_hits = db_query
    if from_ is not None:
        db_query_hits = db_query_hits.offset(from_)
    if size is not None:
        db_query_hits = db_query_hits.limit(size)
    hits = db_query_hits.all()
    count = db_query.count()

    response = utils.build_response_body(facets=facets, hits=hits, count=count)

    return response
