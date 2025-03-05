import sqlalchemy as sa
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import contains_eager

from app.db.auth import constrain_entity_query_to_project, constrain_to_accessible_entities
from app.db.model import Contribution, Entity
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.logger import L
from app.schemas.contribution import ContributionCreate, ContributionRead
from app.schemas.types import ListResponse, PaginationResponse

router = APIRouter(
    prefix="/contribution",
    tags=["contribution"],
)


@router.get("")
def read_contributions(
    db: SessionDep,
    project_context: VerifiedProjectContextHeader,
    pagination_request: PaginationQuery,
) -> ListResponse[ContributionRead]:
    query = constrain_to_accessible_entities(
        sa.select(Contribution).join(Entity).options(contains_eager(Contribution.entity)),
        project_context.project_id,
    )

    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

    response = ListResponse[ContributionRead](
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


@router.get("/{id_}", response_model=ContributionRead)
def read_contribution(id_: int, project_context: VerifiedProjectContextHeader, db: SessionDep):
    with ensure_result(error_message="Contribution not found"):
        stmt = constrain_to_accessible_entities(
            sa.select(Contribution)
            .filter(Contribution.id == id_)
            .join(Contribution.entity)
            .options(contains_eager(Contribution.entity)),
            project_context.project_id,
        )

        row = db.execute(stmt).scalar_one()

    return ContributionRead.model_validate(row)


@router.post("", response_model=ContributionRead)
def create_contribution(
    contribution: ContributionCreate, project_context: VerifiedProjectContextHeader, db: SessionDep
):
    stmt = constrain_entity_query_to_project(
        sa.select(Entity).filter(Entity.id == contribution.entity_id), project_context.project_id
    ).with_only_columns(sa.func.count())
    if db.execute(stmt).scalar_one() == 0:
        L.warning("Attempting to create an annotation for an entity inaccessible to user")
        raise HTTPException(
            status_code=404, detail=f"Cannot access entity {contribution.entity_id}"
        )

    row = Contribution(
        agent_id=contribution.agent_id,
        role_id=contribution.role_id,
        entity_id=contribution.entity_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return row
