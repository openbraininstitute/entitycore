import sqlalchemy as sa
from fastapi import APIRouter

from app.db.auth import constrain_to_accessible_entities
from app.db.model import ExperimentalSynapsesPerConnection
from app.dependencies import PaginationQuery
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.routers.types import ListResponse, PaginationResponse
from app.schemas.density import (
    ExperimentalSynapsesPerConnectionCreate,
    ExperimentalSynapsesPerConnectionRead,
)

router = APIRouter(
    prefix="/experimental-synapses-per-connection",
    tags=["experimental_synapses_per_connection"],
)


@router.get("/", response_model=ListResponse[ExperimentalSynapsesPerConnectionRead])
def get(
    project_context: VerifiedProjectContextHeader,
    db: SessionDep,
    pagination_request: PaginationQuery,
):
    query = constrain_to_accessible_entities(
        sa.select(ExperimentalSynapsesPerConnection), project_context.project_id
    )

    data = db.execute(
        query.offset(pagination_request.page * pagination_request.page_size).limit(
            pagination_request.page_size
        )
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

    response = ListResponse[ExperimentalSynapsesPerConnectionRead](
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


@router.get("/{id_}", response_model=ExperimentalSynapsesPerConnectionRead)
def read_experimental_synapses_per_connection(
    project_context: VerifiedProjectContextHeader,
    id_: int,
    db: SessionDep,
):
    with ensure_result(error_message="ExperimentalSynapsesPerConnection not found"):
        stmt = constrain_to_accessible_entities(
            sa.select(ExperimentalSynapsesPerConnection).filter(
                ExperimentalSynapsesPerConnection.id == id_
            ),
            project_context.project_id,
        )
        row = db.execute(stmt).scalar_one()

    return ExperimentalSynapsesPerConnectionRead.model_validate(row)


@router.post("/", response_model=ExperimentalSynapsesPerConnectionRead)
def create_experimental_synapses_per_connection(
    project_context: VerifiedProjectContextHeader,
    density: ExperimentalSynapsesPerConnectionCreate,
    db: SessionDep,
):
    dump = density.model_dump()

    row = ExperimentalSynapsesPerConnection(
        **dump, authorized_project_id=project_context.project_id
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
