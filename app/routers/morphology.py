from typing import Annotated

import sqlalchemy as sa
from fastapi import APIRouter
from fastapi_filter import FilterDepends
from sqlalchemy.orm import Session, contains_eager, joinedload

from app.db.auth import constrain_to_accessible_entities
from app.db.model import (
    AnnotationMType,
    Base,
    BrainLocation,
    MTypeAnnotationBody,
    ReconstructionMorphology,
    Species,
    Strain,
)
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.morphology import MorphologyFilter
from app.routers.types import Facet, Facets, ListResponse, Pagination
from app.schemas.morphology import (
    ReconstructionMorphologyCreate,
    ReconstructionMorphologyExpand,
    ReconstructionMorphologyRead,
)

router = APIRouter(
    prefix="/reconstruction_morphology",
    tags=["reconstruction_morphology"],
)


@router.get(
    "/{rm_id}",
    response_model=ReconstructionMorphologyExpand | ReconstructionMorphologyRead,
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
            .options(joinedload(ReconstructionMorphology.license))
            .options(joinedload(ReconstructionMorphology.species))
            .options(joinedload(ReconstructionMorphology.strain))
        )

        row = query.one()

    if expand and "morphology_feature_annotation" in expand:
        return ReconstructionMorphologyExpand.model_validate(row)

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

    db_reconstruction_morphology = ReconstructionMorphology(
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
    db.add(db_reconstruction_morphology)
    db.commit()
    db.refresh(db_reconstruction_morphology)
    return db_reconstruction_morphology


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


def _get_facet_mtypes(
    db: SessionDep,
    query,
) -> list[Facet]:
    facet_q = (
        query.join(AnnotationMType, ReconstructionMorphology.id == AnnotationMType.entity_id)
        .join(MTypeAnnotationBody)
        .with_only_columns(MTypeAnnotationBody, sa.func.count().label("count"))
        .group_by(MTypeAnnotationBody)  # type: ignore[arg-type]
        .order_by(MTypeAnnotationBody.pref_label)  # type: ignore[attr-defined]
    )

    return [
        Facet(id=row.id, label=row.pref_label, count=count, type=row.type)
        for row, count in db.execute(facet_q).all()
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
    )

    if search:
        # query = query.filter(ReconstructionMorphology.morphology_description_vector.match(search))
        query = query.where(ReconstructionMorphology.morphology_description_vector.match(search))

    query = morphology_filter.filter(query)

    facets = _get_facets(db, query, name_to_table)
    facets["mtypes"] = _get_facet_mtypes(db, query)

    query = (
        query.options(contains_eager(ReconstructionMorphology.species))
        .options(contains_eager(ReconstructionMorphology.strain))
        .options(joinedload(ReconstructionMorphology.license))
        .options(joinedload(ReconstructionMorphology.brain_region))
        .options(joinedload(ReconstructionMorphology.brain_location))
    )

    data = db.execute(
        morphology_filter.sort(query).offset(page * page_size).limit(page_size)
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

    response = ListResponse[ReconstructionMorphologyRead](
        data=data,
        pagination=Pagination(page=page, page_size=page_size, total_items=total_items),
        facets=facets,
    )

    return response
