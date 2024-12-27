from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import aliased

import app.models.annotation
import app.models.base
import app.models.morphology
from app.models import agent, annotation, base, contribution, morphology

MAP_TYPES = {
    app.models.base.License: "License",
    app.models.annotation.MTypeAnnotationBody: "Class",
    app.models.annotation.ETypeAnnotationBody: "Class",
    app.models.base.Species: "Species",
    app.models.morphology.ReconstructionMorphology: "https://neuroshapes.org/ReconstructedNeuronMorphology",
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


def get_facets(aggs, db_type, db):
    if not aggs:
        return {}   
    facets = {}
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
        facet_q = db.query(getattr(cur_alias, group_name), func.count().label("count"))
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
    print(ret)
    return ret


def build_count_response_body(value):
    return {
        "hits": {"hits": [], "total": {"relation": "eq", "value": value}},
        "terminated_early": False,
        "timed_out": False,
        "took": 13,
        "_shards": {"failed": 0, "skipped": 4, "successful": 15, "total": 15},
    }
