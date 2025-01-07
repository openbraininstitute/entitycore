from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import aliased
from bidict import bidict as bdict
import app.models.annotation
import app.models.base
import app.models.code
import app.models.density
import app.models.emodel
import app.models.entity
import app.models.memodel
import app.models.mesh
import app.models.morphology
import app.models.single_cell_experimental_trace
from app.models import agent, annotation, base, contribution, entity
import app.models.single_neuron_synaptome
import app.models.single_neuron_simulation

MAP_TYPES = bdict(
    {
        app.models.base.License: "License",
        # app.models.annotation.MTypeAnnotationBody: "Class",
        # app.models.annotation.ETypeAnnotationBody: "Class",
        app.models.base.Species: "Species",
        app.models.morphology.ReconstructionMorphology: "https://neuroshapes.org/ReconstructedNeuronMorphology",
        app.models.density.ExperimentalBoutonDensity: "https://bbp.epfl.ch/ontologies/core/bmo/ExperimentalBoutonDensity",
        app.models.density.ExperimentalNeuronDensity: "https://bbp.epfl.ch/ontologies/core/bmo/ExperimentalNeuronDensity",
        app.models.MEModel: "https://neuroshapes.org/MEModel",
        app.models.EModel: "https://neuroshapes.org/EModel",
        app.models.mesh.Mesh: "Mesh",
        app.models.single_cell_experimental_trace.SingleCellExperimentalTrace: "https://bbp.epfl.ch/ontologies/core/bmo/ExperimentalTrace",
        app.models.density.ExperimentalSynapsesPerConnection: "https://bbp.epfl.ch/ontologies/core/bmo/ExperimentalSynapsesPerConnection",
        app.models.code.AnalysisSoftwareSourceCode: "AnalysisSoftwareSourceCode",
        app.models.single_neuron_synaptome.SingleNeuronSynaptome: "https://bbp.epfl.ch/ontologies/core/bmo/SingleNeuronSynaptome",
        app.models.single_neuron_simulation.SingleNeuronSimulation: "SingleNeuronSimulation",
    }
)

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


def get_db_type(query):
    terms = query.get("query", {}).get("bool", {}).get("must", [])
    if not terms:
        return entity.Entity
    if type(terms) is not list:
        terms = [terms]
    type_term = [term for term in terms if "@type.keyword" in term.get("term", {})]
    if not type_term:
        type_term = [term for term in terms if "@type" in term.get("term", {})]
        if not type_term:
            return entity.Entity
    type_keyword = type_term[0].get("term", {}).get("@type.keyword", "")
    if not type_keyword:
        type_keyword = type_term[0].get("term", {}).get("@type", "")
    db_type = MAP_TYPES.inv[type_keyword]
    return db_type


QUERY_PATH = {
    "mType": {
        "models": [annotation.Annotation, annotation.MTypeAnnotationBody],
        "joins": [("id", "entity_id"), ("annotation_body_id", "id")],
    },
    "eType": {
        "models": [annotation.Annotation, annotation.ETypeAnnotationBody],
        "joins": [("id", "entity_id"), ("annotation_body_id", "id")],
    },
    "brainRegion": {"models": [base.BrainRegion], "joins": [("brain_region_id", "id")]},
    "subjectSpecies": {"models": [base.Species], "joins": [("species_id", "id")]},
    "contributors": {
        "models": [contribution.Contribution, agent.Agent],
        "joins": [("id", "entity_id"), ("agent_id", "id")],
    },
    "createdBy": {
        "models": [agent.Agent],
        "joins": [("createdBy_id", "id")],
    },
}
PROPERTY_MAP = {
    "mType.label": "pref_label",
    "eType.label": "pref_label",
    "brainRegion.@id": "ontology_id",
    "subjectSpecies.label": "name",
    "contributors.label": "pref_label",
    "@id": "legacy_id",
    "createdBy.label": "pref_label",
}


def get_facets(aggs, musts, db_type, db):
    if not aggs:
        return {}
    facets = {}
    # stats: only min and max matters.
    # not used for createdAt and updatedAt in GUI

    fields = [
        {"label": key, "field": aggs[key]["terms"]["field"]}
        for key in aggs.keys()
        if "terms" in aggs[key]
    ]
    for field in fields:
        # TODO understand how link is created
        if "emodel.neuronMorphology" in field["field"]:
            continue
        split_field = field["field"].split(".")
        target = split_field[0]
        if len(split_field) > 2:
            property_ = split_field[1]
        else:
            property_ = "label"
        query_map = QUERY_PATH.get(target)
        joins = list(reversed(query_map["joins"]))
        models = list(reversed(query_map["models"]))

        models.append(aliased(db_type))
        cur_alias = aliased(list(models)[0])
        initial_alias = cur_alias
        property_group = PROPERTY_MAP.get(".".join([target, property_]), None)
        facet_q = db.query(
            getattr(initial_alias, property_group), func.count().label("count")
        )
        for model, join in zip(models[1:], joins):
            prev_alias = cur_alias
            cur_alias = aliased(model)
            facet_q = facet_q.join(
                cur_alias,
                getattr(prev_alias, join[1]) == getattr(cur_alias, join[0]),
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
    try:
        mapping = {**MAPPING_PER_TYPE.get(elem.__class__, {}), **MAPPING_GLOBAL}
        for key, value in mapping.items():
            initial_dict[value] = jsonable_encoder(getattr(elem, key, ""))
        if elem.__class__ in [
            app.models.annotation.MTypeAnnotationBody,
            app.models.annotation.ETypeAnnotationBody,
        ]:
            initial_dict["@type"] = "Class"
        else:
            initial_dict["@type"] = [MAP_TYPES[elem.__class__]]
        initial_dict["@id"] = elem.legacy_id[0]
    except Exception as e:
        print(e)
        print(elem)
        raise e
    return {
        "_id": elem.legacy_id[0],
        "_index": "dummy",
        "_score": 1.0,
        "_source": initial_dict,
    }


def find_term_keys(data):
    """
    Recursively find all keys named "term", "terms" or "wildcard" in the dictionary `data`,
    :return: List of keys found.
    """
    result = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in ["term", "terms", "wildcard"]:
                result.append({key: value})
            else:
                result.extend(find_term_keys(value))
    elif isinstance(data, list):
        for item in data:
            result.extend(find_term_keys(item))
    return result


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
            if key in [
                "@type.keyword",
                "deprecated",
                "curated",
                "@type",
                "_deprecated",
                "atlasRelease.@id",
            ]:
                continue
            else:
                if key == "@id":
                    query = query.filter(
                        base.StringList.in_(initial_alias.legacy_id, [value])
                    )
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
            if "." in key:
                target, property_, _ = key.split(".")
                if db_type == app.models.entity.Entity:
                    if property_ == "@id":
                        property_ = "legacy_id"
                        cur_alias = initial_alias
                else:
                    query_map = QUERY_PATH.get(target, None)
                    property_ = PROPERTY_MAP.get(".".join([target, property_]), None)
                    if not query_map or not property_:
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
                        raise HTTPException(status_code=500, detail="unexpected error")

            else:
                cur_alias = initial_alias
                if key == "_id":
                    property_ = "legacy_id"
                else:
                    property_ = PROPERTY_MAP.get(key, key.replace(".label", ""))
            column = getattr(cur_alias, property_)

            if type(value) is not list:
                value = [value]
            if property_ == "legacy_id":
                query = query.filter(base.StringList.in_(column, value))
            else:
                query = query.filter(column.in_(value))
        elif "wildcard" in must_term:
            # TODO check if this is always hardcoded
            value = must_term["wildcard"]["name.keyword"]["value"]
            # TODO: remove hardcoded morphology_description_vector
            query = query.filter(db_type.morphology_description_vector.match(value))

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
