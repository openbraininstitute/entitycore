import app.models.base as models
from sqlalchemy import and_
import app.routers.legacy.model.utils as utils

def build_filters(model, filter_dict):
    filters = []
    for key, value in filter_dict.items():
        column = getattr(model, key, None)
        if column is not None:
            filters.append(column == value)
    return filters



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
        return utils.build_response_body(query.all())
    finally:
        db.close()
