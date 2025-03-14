from sqlalchemy import and_

from app.db.model import License
from app.routers.legacy.model import utils


def build_filters(model, filter_dict):
    filters = []
    for key, value in filter_dict.items():
        column = getattr(model, key, None)
        if column is not None:
            filters.append(column == value)
    return filters


def search(body, db):
    terms = body.get("query", {}).get("bool", {}).get("must", [])
    whitelist_terms = {"@id": "name"}
    acceptable_terms = [
        term for term in terms if next(iter(term.get("term").keys())) in whitelist_terms
    ]
    filters = build_filters(
        License,
        {
            whitelist_terms[next(iter(term.get("term", {}).keys()))]: next(
                iter(term.get("term", {}).values())
            )
            for term in acceptable_terms
        },
    )
    try:
        query = db.query(License).filter(and_(*filters))
        return utils.build_response_body(hits=query.all(), count=len(query.all()))
    finally:
        db.close()
