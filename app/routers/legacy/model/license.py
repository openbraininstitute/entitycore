import app.models.base as models
from sqlalchemy import and_


def build_filters(model, filter_dict):
    filters = []
    for key, value in filter_dict.items():
        column = getattr(model, key, None)
        if column is not None:
            filters.append(column == value)
    return filters


def build_response_elem(elem):
    MAPPING = {
        "name": "@id",
        "creation_date": "_createdAt",
        "updated_date": "_updatedAt",
        "description": "description",
        "label": "label",
    }

    initial_dict = {
        "_constrainedBy": "https://bluebrain.github.io/nexus/schemas/unconstrained.json",
        "_createdAt": "224-01-10T15:58:46.007611Z",
        "_deprecated": False,
        "_project": "https://openbluebrain.com/api/nexus/v1/projects/bbp/licenses",
        "_rev": 0,
        "_schemaProject": "https://openbluebrain.com/api/nexus/v1/projects/bbp/licenses",
        "_updatedBy": "https://openbluebrain.com/api/nexus/v1/realms/bbp/users/cgonzale",
    }
    for key, value in MAPPING.items():
        initial_dict[value] = getattr(elem, key, "")
    initial_dict["@type"] = ["License"]
    return {
        "_id": getattr(elem, "name"),
        "_index": "dummy",
        "_score": 1.0,
        "_source": initial_dict,
    }


def build_response_body(elems):
    return {
        "hits": {
            "hits": [build_response_elem(elem) for elem in elems],
            "timed_out": False,
            "took": 2,
            "_shards": {"failed": 0, "skipped": 0, "successful": 6, "total": 6},
        }
    }


def search(body, db):
    terms = body.get("query", {}).get("bool", {}).get("must", [])
    WHITELIST_TERMS = {"@id": "name"}
    acceptable_terms = [
        term
        for term in terms
        if list(term.get("term").keys())[0] in WHITELIST_TERMS.keys()
    ]
    filters = build_filters(
        models.License,
        {
            WHITELIST_TERMS[list(term.get("term", {}).keys())[0]]: list(
                term.get("term", {}).values()
            )[0]
            for term in acceptable_terms
        },
    )
    try:
        query = db.query(models.License).filter(and_(*filters))
        return build_response_body(query.all())
    finally:
        db.close()
