from typing import Annotated

import sqlalchemy as sa
from fastapi import APIRouter
from fastapi_filter import FilterDepends
from sqlalchemy.orm import Session, joinedload, aliased

from app.db.auth import constrain_to_accessible_entities
from app.db.model import (
    Agent,
    Base,
    BrainLocation,
    Contribution,
    ReconstructionMorphology,
    Species,
    Strain,
    Root,
)
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.morphology import MorphologyFilter
from app.routers.types import Facet, Facets, ListResponse, Pagination
from app.schemas.morphology import (
    ReconstructionMorphologyAnnotationExpandedRead,
    ReconstructionMorphologyCreate,
    ReconstructionMorphologyRead,
)

router = APIRouter(
    prefix="/reconstruction_morphology",
    tags=["reconstruction_morphology"],
)


@router.get(
    "/{rm_id}",
    response_model=ReconstructionMorphologyRead | ReconstructionMorphologyAnnotationExpandedRead,
)
def read_reconstruction_morphology(
    db: SessionDep,
    rm_id: int,
    project_context: VerifiedProjectContextHeader,
    expand: str | None = None,
):
    with ensure_result(error_message="ReconstructionMorphology not found"):
        query = constrain_to_accessible_entities(
            db.query(ReconstructionMorphology), project_context.project_id
        ).filter(ReconstructionMorphology.id == rm_id)

        if expand and "morphology_feature_annotation" in expand:
            query = query.options(
                joinedload(ReconstructionMorphology.morphology_feature_annotation)
            )

        query = (
            query.options(joinedload(ReconstructionMorphology.brain_location))
            .options(joinedload(ReconstructionMorphology.brain_region))
            .options(joinedload(ReconstructionMorphology.contributors))
            .options(joinedload(ReconstructionMorphology.license))
            .options(joinedload(ReconstructionMorphology.species))
            .options(joinedload(ReconstructionMorphology.strain))
        )

        row = query.one()

    if expand and "morphology_feature_annotation" in expand:
        return ReconstructionMorphologyAnnotationExpandedRead.model_validate(row)

    # added back with None by the response_model
    return ReconstructionMorphologyRead.model_validate(row)


@router.post("/", response_model=ReconstructionMorphologyRead)
def create_reconstruction_morphology(
    project_context: VerifiedProjectContextHeader,
    reconstruction: ReconstructionMorphologyCreate,
    db: SessionDep,
):
    brain_location = None

    if reconstruction.brain_location:
        brain_location = BrainLocation(**reconstruction.brain_location.model_dump())

    db_rm = ReconstructionMorphology(
        name=reconstruction.name,
        description=reconstruction.description,
        brain_location=brain_location,
        brain_region_id=reconstruction.brain_region_id,
        species_id=reconstruction.species_id,
        strain_id=reconstruction.strain_id,
        license_id=reconstruction.license_id,
        authorized_project_id=project_context.project_id,
        authorized_public=reconstruction.authorized_public,
    )
    db.add(db_rm)
    db.commit()
    db.refresh(db_rm)

    return db_rm


def _get_facets(
    db: Session,
    query: sa.Select,
    name_to_table: dict[str, type[Base]],
) -> Facets:
    facets = {}

    for name, table in name_to_table.items():
        facet_q = (
            query.with_only_columns(table, sa.func.count().label("count"))
            .group_by(table)  # type: ignore[arg-type]
            .order_by(table.name)  # type: ignore[attr-defined]
        )
        facets[name] = [
            Facet(id=row.id, label=row.name, count=count, type=name)
            for row, count in db.execute(facet_q).all()
            if row is not None  # exclude null rows
        ]

    return facets


def _get_facet_contributor(
    db: SessionDep,
    query: sa.Select,
) -> list[Facet]:
    subq = query.join(Agent).subquery()

    facet_q = (
        sa.select(Agent)
        .join(Contribution)
        .join(subq, Contribution.entity_id == subq.c.id)
        .with_only_columns(Agent.id, Agent.pref_label, Agent.type, sa.func.count().label("count"))
        .group_by(Agent.id, Agent.pref_label, Agent.type)  # type: ignore[arg-type]
    )
    return [
        Facet(id=id_, label=pref_label, type=type_, count=count)
        for id_, pref_label, type_, count in db.execute(facet_q).all()
    ]


@router.get("/", response_model=ListResponse[ReconstructionMorphologyRead])
def morphology_query(
    db: SessionDep,
    project_context: VerifiedProjectContextHeader,
    morphology_filter: Annotated[MorphologyFilter, FilterDepends(MorphologyFilter)],
    search: str | None = None,
    page: int = 0,
    page_size: int = 10,
):
    name_to_table = {
        "species": Species,
        "strain": Strain,
    }

    query = (
        constrain_to_accessible_entities(
            sa.select(ReconstructionMorphology), project_context.project_id
        )
        .join(Species, ReconstructionMorphology.species_id == Species.id)
        .outerjoin(Strain, ReconstructionMorphology.strain_id == Strain.id)
        .outerjoin(Contribution, ReconstructionMorphology.id == Contribution.entity_id)
        #.outerjoin(Agent, Agent.id == Contribution.agent_id)
    )

    if search:
        query = query.where(ReconstructionMorphology.morphology_description_vector.match(search))

    query = morphology_filter.filter(query)

    #facets = _get_facets(db, query, name_to_table)
    facets = {}
    facets["contributors"] = _get_facet_contributor(db, query)

    query = (
        query.options(joinedload(ReconstructionMorphology.brain_location))
        .options(joinedload(ReconstructionMorphology.brain_region))
        .options(joinedload(ReconstructionMorphology.license))
        .options(joinedload(ReconstructionMorphology.species))
        .options(joinedload(ReconstructionMorphology.strain))
        .options(joinedload(ReconstructionMorphology.contributors))
    )

    data = db.execute(
        morphology_filter.sort(query).offset(page * page_size).limit(page_size)
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

    response = ListResponse[ReconstructionMorphologyRead](
        data=data.unique(),
        pagination=Pagination(page=page, page_size=page_size, total_items=total_items),
        facets=facets,
    )

    return response
