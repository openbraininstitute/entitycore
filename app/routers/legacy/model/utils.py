from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import aliased

import app.models.annotation
import app.models.base
import app.models.density
import app.models.morphology
import app.models.single_cell_experimental_trace
import app.models.memodel
from app.models import agent, annotation, base, contribution

MAP_TYPES = {
    app.models.base.License: "License",
    app.models.annotation.MTypeAnnotationBody: "Class",
    app.models.annotation.ETypeAnnotationBody: "Class",
    app.models.base.Species: "Species",
    app.models.morphology.ReconstructionMorphology: "https://neuroshapes.org/ReconstructedNeuronMorphology",
    app.models.ExperimentalBoutonDensity: "https://neuroshapes.org/ExperimentalBoutonDensity",
    app.models.ExperimentalNeuronDensity: "https://neuroshapes.org/ExperimentalNeuronDensity",
}

MAPPING_GLOBAL = {
    "creation_date": "_createdAt",
    "updated_date": "_updatedAt",
}
MAPPING_PER_TYPE = {
    app.models.base.License: {
        "name": "@id",
        "description": "description",
        "label": "label",
    },
    app.models.annotation.ETypeAnnotationBody: {
        "pref_label": "label",
        "definition": "definition",
    },
    app.models.annotation.MTypeAnnotationBody: {
        "pref_label": "label",
        "definition": "definition",
    },
}

MAP_KEYWORD = {
    "https://neuroshapes.org/ReconstructedNeuronMorphology": app.models.morphology.ReconstructionMorphology,
    "https://bbp.epfl.ch/ontologies/core/bmo/ExperimentalTrace": app.models.single_cell_experimental_trace.SingleCellExperimentalTrace,
    "https://bbp.epfl.ch/ontologies/core/bmo/ExperimentalNeuronDensity": app.models.density.ExperimentalNeuronDensity,
    "https://bbp.epfl.ch/ontologies/core/bmo/ExperimentalBoutonDensity": app.models.density.ExperimentalBoutonDensity,
    "https://bbp.epfl.ch/ontologies/core/bmo/ExperimentalSynapsesPerConnection": app.models.density.ExperimentalSynapsesPerConnection,
    "https://neuroshapes.org/MEModel": app.models.memodel.MEModel,
}


def get_db_type(query):
    try:
        terms = query.get("query", {}).get("bool", {}).get("must", [])
        type_term = [term for term in terms if "@type.keyword" in term.get("term", {})]
        type_keyword = type_term[0].get("term", {}).get("@type.keyword", "")
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Bad request: query must contain a type",
        )

    db_type = MAP_KEYWORD.get(type_keyword)
    return db_type


QUERY_PATH = {
    "mType": {
        "models": [annotation.Annotation, annotation.MTypeAnnotationBody],
        "joins": [("id", "entity_id"), ("annotation_body_id", "id")],
    },
    "brainRegion": {"models": [base.BrainRegion], "joins": [("brain_region_id", "id")]},
    "subjectSpecies": {"models": [base.Species], "joins": [("species_id", "id")]},
    "contributors": {
        "models": [contribution.Contribution, agent.Agent],
        "joins": [("id", "entity_id"), ("agent_id", "id")],
    },
}
PROPERTY_MAP = {
    "mType.label": "pref_label",
    "brainRegion.@id": "ontology_id",
    "subjectSpecies.label": "name",
    "contributors.label": "pref_label",
}

def get_facets(aggs, musts, db_type, db):
    if not aggs:
        return {}
    facets = {}
    # stats: only min and max matters.
    # not used for createdAt and updatedAt in GUI

    fields = [
        {"label": key, "field": aggs[key]["terms"]["field"]} for key in aggs.keys() if "terms" in aggs[key]
    ]
    for field in fields:
        target,property,_= field["field"].split(".")
        query_map = QUERY_PATH.get(target)
        joins = list(reversed(query_map["joins"]))
        models = list(reversed(query_map["models"]))

        models.append(aliased(db_type))
        cur_alias = aliased(list(models)[0])
        initial_alias = cur_alias
        property_group = PROPERTY_MAP.get(".".join([target, property]), None)        
        facet_q = db.query(getattr(initial_alias, property_group), func.count().label("count"))
        for model, join in zip(models[1:], joins):
            prev_alias = cur_alias
            cur_alias = aliased(model)
            facet_q = facet_q.join(
                cur_alias,
                getattr(prev_alias, join[1])
                == getattr(cur_alias, join[0]),
            )

        alias = cur_alias
        facet_q = add_predicates_to_query(facet_q, musts, db_type, alias)
        facet_q = facet_q.group_by(getattr(initial_alias, property_group))
        facet_q = facet_q.order_by(func.count().desc())
        facets[field["label"]] = facet_q.all()
    return facets


def build_response_elem(elem):
    initial_dict = {
        "_constrainedBy": "https://bluebrain.github.io/nexus/schemas/unconstrained.json",
        "_deprecated": False,
        "_project": "https://openbluebrain.com/api/nexus/v1/projects/bbp/licenses",
        "_rev": 0,
        "_schemaProject": "https://openbluebrain.com/api/nexus/v1/projects/bbp/licenses",
        "_updatedBy": "https://openbluebrain.com/api/nexus/v1/realms/bbp/users/cgonzale",
    }
    mapping = {**MAPPING_PER_TYPE.get(elem.__class__, {}), **MAPPING_GLOBAL}
    for key, value in mapping.items():
        initial_dict[value] = jsonable_encoder(getattr(elem, key, ""))
    initial_dict["@type"] = [MAP_TYPES[elem.__class__]]
    initial_dict["@id"] = elem.legacy_id[0]
    return {
        "_id": elem.legacy_id[0],
        "_index": "dummy",
        "_score": 1.0,
        "_source": initial_dict,
    }


def add_predicates_to_query(query, must_terms, db_type, alias=None):
    initial_alias = alias or db_type
    for must_term in must_terms:
        if "term" in must_term:
            key_value = must_term["term"].items()
            if len(key_value) != 1:
                raise HTTPException(
                    status_code=400,
                    detail="Bad request: query must contain only one term",
                )

            key, value = list(key_value)[0]
            # deprecated & curated are not a field in the database
            if key in ["@type.keyword", "deprecated", "curated"]:
                continue
            else:
                query = query.filter(getattr(db_type, key) == value)
        elif "terms" in must_term:
            key_value = must_term["terms"].items()

            if len(key_value) != 1:
                raise HTTPException(
                    status_code=400,
                    detail="Bad request: query must contain only one term",
                )
            key, value = list(key_value)[0]
            target, property, _ = key.split(".")
            query_map = QUERY_PATH.get(target, None)
            property = PROPERTY_MAP.get(".".join([target, property]), None)
            if not query_map or not property:
                raise HTTPException(
                    status_code=500,
                    detail="not implemented",
                )
            prev_alias = initial_alias
            cur_alias = None
            for model, join in zip(query_map["models"], query_map["joins"]):
                cur_alias = aliased(model)
                query = query.join(
                    cur_alias,
                    getattr(cur_alias, join[1]) == getattr(prev_alias, join[0]),
                )
                prev_alias = cur_alias
            if not cur_alias:
                raise HTTPException(
                    status_code=500,
                    detail="unexpected error",
                )
            query = query.filter(getattr(cur_alias, property).in_(value))
        else:
            raise HTTPException(
                status_code=400, detail="Bad request: query does not contain any term"
            )
    return query


def build_aggregations(facets):
    ret = {}
    for k, v in facets.items():
        ret[k] = {"buckets": [{"key": elem[0], "doc_count": elem[1]} for elem in v]}
    return ret


def build_hits(hits, count, build_func):
    return {
        "hits": [build_func(elem) for elem in hits],
        "total": {"relation": "eq", "value": count},
    }


def build_response_body(
    facets=None, hits=None, count=-1, build_func=build_response_elem
):
    response = {}
    if facets:
        response["aggregations"] = build_aggregations(facets)
    response["hits"] = build_hits(hits=hits, count=count, build_func=build_func)
    ret = JSONResponse(content=jsonable_encoder(response))
    return ret


def build_count_response_body(value):
    return {
        "hits": {"hits": [], "total": {"relation": "eq", "value": value}},
        "terminated_early": False,
        "timed_out": False,
        "took": 13,
        "_shards": {"failed": 0, "skipped": 4, "successful": 15, "total": 15},
    }
