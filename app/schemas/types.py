from typing import Annotated

import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict, Field, computed_field
from sqlalchemy.orm import InstrumentedAttribute, Query, Session


class PaginationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: Annotated[int, Field(ge=1)] = 1
    page_size: Annotated[int, Field(ge=1)] = 100

    @computed_field  # type: ignore[prop-decorator]
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    def paginate_query(self, q: Query | sa.Select):
        return q.limit(self.page_size).offset(self.offset)

    def paginated_rows(self, db: Session, q: Query | sa.Select):
        q = self.paginate_query(q)
        return db.execute(q)

    def pagination(self, db: Session, q: Query | sa.Select, distinct_col: InstrumentedAttribute):
        total_items = db.execute(
            q.with_only_columns(sa.func.count(sa.func.distinct(distinct_col)).label("count"))
        ).scalar_one()

        return PaginationResponse(page=self.page, page_size=self.page_size, total_items=total_items)


class PaginationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page: int
    page_size: int
    total_items: int


class Facet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    count: int
    type: str | None


type Facets = dict[str, list[Facet]]


class ListResponse[M: BaseModel](BaseModel):
    data: list[M]
    pagination: PaginationResponse
    facets: Facets | None = None
