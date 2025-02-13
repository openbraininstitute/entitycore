from typing import Annotated

from fastapi import APIRouter, Request
from fastapi_filter import FilterDepends
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from app.db.auth import constrain_to_accessible_entities
from app.db.model import (
    Base,
    BrainLocation,
    ReconstructionMorphology,
    Species,
    Strain,
)
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.filters.morphology import MorphologyFilter
from app.routers.types import Facets, ListResponse, Pagination
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
        rm = (
            constrain_to_accessible_entities(
                db.query(ReconstructionMorphology), project_context.project_id
            )
            .filter(ReconstructionMorphology.id == rm_id)
            .one()
        )

    if expand and "morphology_feature_annotation" in expand:
        return ReconstructionMorphologyExpand.model_validate(rm)

    # added back with None by the response_model
    return ReconstructionMorphologyRead.model_validate(rm)


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
    name_to_table: dict[str, type[Base]],
    request: Request,
    search: str | None,
):
    facets: Facets = {}
    for ty, table in name_to_table.items():
        types = aliased(table)
        # TODO: this should be migrated to sqlalchemy v2.0 style:
        # https://github.com/openbraininstitute/entitycore/pull/11#discussion_r1935703476
        facet_q = (
            db.query(types.name, func.count().label("total"))  # type: ignore[attr-defined]
            .join(
                ReconstructionMorphology,
                getattr(ReconstructionMorphology, ty + "_id") == types.id,  # type: ignore[attr-defined]
            )
            .group_by(types.name)  # type: ignore[attr-defined]
        )
        if search:
            facet_q = facet_q.filter(
                ReconstructionMorphology.morphology_description_vector.match(search)
            )

        for other_ty, other_table in name_to_table.items():
            if value := request.query_params.get(other_ty, None):
                other_types = aliased(other_table)
                facet_q = facet_q.join(
                    other_types,
                    getattr(ReconstructionMorphology, other_ty + "_id") == other_types.id,  # type: ignore[attr-defined]
                ).where(other_types.name == value)  # type: ignore[attr-defined]
        facets[ty] = {r.name: r.total for r in facet_q.all()}

    return facets


@router.get("/", response_model=ListResponse[ReconstructionMorphologyRead])
def morphology_query(
    request: Request,
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

    facets = _get_facets(db, name_to_table, request, search)

    if search is None and not any(ty in request.query_params for ty in name_to_table):
        query = db.query(ReconstructionMorphology)
        query = constrain_to_accessible_entities(query, project_context.project_id)
        query = morphology_filter.filter(query)
        response = ListResponse[ReconstructionMorphologyRead](
            data=morphology_filter.sort(query).offset(page * page_size).limit(page_size).all(),
            pagination=Pagination(page=page, page_size=page_size, total_items=query.count()),
            facets=facets,
        )
    else:
        query = db.query(ReconstructionMorphology)
        query = constrain_to_accessible_entities(query, project_context.project_id)
        rms = (
            query.where(ReconstructionMorphology.morphology_description_vector.match(search))
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )

        response = ListResponse[ReconstructionMorphologyRead](
            data=[ReconstructionMorphologyRead.model_validate(rm) for rm in rms],
            pagination=Pagination(page=page, page_size=page_size, total_items=query.count()),
            facets=facets,
        )

    return response
