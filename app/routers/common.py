from typing import Annotated, NotRequired, TypedDict

import sqlalchemy as sa
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import (
    InstrumentedAttribute,
    Session,
)

from app.schemas.types import Facet, Facets


class FacetQueryParams(TypedDict):
    id: InstrumentedAttribute[int]
    label: InstrumentedAttribute[str]
    type: NotRequired[InstrumentedAttribute[str]]


def get_facets(
    db: Session,
    query: sa.Select,
    name_to_facet_query_params: dict[str, FacetQueryParams],
    count_distinct_field: InstrumentedAttribute,
) -> Facets:
    facets = {}
    groupby_keys = ["id", "label", "type"]
    orderby_keys = ["label"]
    for facet_type, fields in name_to_facet_query_params.items():
        groupby_fields = {"type": sa.literal(facet_type), **fields}
        groupby_columns = [groupby_fields[key].label(key) for key in groupby_keys]  # type: ignore[attr-defined]
        groupby_ids = [sa.literal(i + 1) for i in range(len(groupby_columns))]
        facet_q = (
            query.with_only_columns(
                *groupby_columns,
                sa.func.count(sa.func.distinct(count_distinct_field)).label("count"),
            )
            .group_by(*groupby_ids)
            .order_by(*orderby_keys)
        )
        facets[facet_type] = [
            Facet.model_validate(row, from_attributes=True)
            for row in db.execute(facet_q).all()
            if row.id is not None  # exclude null rows if present
        ]

    return facets


class Facets(BaseModel):
    with_facets: bool = False

    def get_facets(self, db, query, name_to_facet_query_params, count_distinct_field):
        if not self.with_facets:
            return None

        return get_facets(db, query, name_to_facet_query_params, count_distinct_field)


class Search(BaseModel):
    search: str | None = None

    def with_search(self, q: sa.Select, vector_col: InstrumentedAttribute):
        if not self.search:
            return q

        return q.where(vector_col.match(self.search))


FacetsDep = Annotated[Facets, Depends()]
SearchDep = Annotated[Search, Depends()]
