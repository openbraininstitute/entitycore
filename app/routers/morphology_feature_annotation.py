import uuid

import sqlalchemy as sa
from fastapi import APIRouter, HTTPException

from app.db.auth import constrain_entity_query_to_project, constrain_to_accessible_entities
from app.db.model import (
    MorphologyFeatureAnnotation,
    MorphologyMeasurement,
    MorphologyMeasurementSerieElement,
    ReconstructionMorphology,
)
from app.dependencies.auth import UserContextDep, UserContextWithProjectIdDep
from app.dependencies.common import PaginationQuery
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.logger import L
from app.schemas.morphology import (
    MorphologyFeatureAnnotationCreate,
    MorphologyFeatureAnnotationRead,
)
from app.schemas.types import ListResponse, PaginationResponse

router = APIRouter(
    prefix="/morphology-feature-annotation",
    tags=["morphology-feature-annotation"],
)


@router.get("")
def read_morphology_feature_annotations(
    user_context: UserContextDep,
    db: SessionDep,
    pagination_request: PaginationQuery,
) -> ListResponse[MorphologyFeatureAnnotationRead]:
    query = constrain_to_accessible_entities(
        sa.select(MorphologyFeatureAnnotation).join(ReconstructionMorphology),
        user_context.project_id,
    )

    data = db.execute(
        query.offset(pagination_request.offset).limit(pagination_request.page_size)
    ).scalars()

    total_items = db.execute(
        query.with_only_columns(sa.func.count(MorphologyFeatureAnnotation.id))
    ).scalar_one()

    response = ListResponse[MorphologyFeatureAnnotationRead](
        data=data,
        pagination=PaginationResponse(
            page=pagination_request.page,
            page_size=pagination_request.page_size,
            total_items=total_items,
        ),
        facets=None,
    )

    return response


@router.get("/{id_}", response_model=MorphologyFeatureAnnotationRead)
def read_morphology_feature_annotation_id(
    user_context: UserContextDep,
    db: SessionDep,
    id_: uuid.UUID,
):
    with ensure_result(error_message="MorphologyFeatureAnnotation not found"):
        stmt = constrain_to_accessible_entities(
            sa.select(MorphologyFeatureAnnotation)
            .filter(MorphologyFeatureAnnotation.id == id_)
            .join(ReconstructionMorphology),
            user_context.project_id,
        )
        row = db.execute(stmt).scalar_one()

    return MorphologyFeatureAnnotationRead.model_validate(row)


@router.post("", response_model=MorphologyFeatureAnnotationRead)
def create_morphology_feature_annotation(
    user_context: UserContextWithProjectIdDep,
    db: SessionDep,
    morphology_feature_annotation: MorphologyFeatureAnnotationCreate,
):
    reconstruction_morphology_id = morphology_feature_annotation.reconstruction_morphology_id

    stmt = constrain_entity_query_to_project(
        sa.select(sa.func.count(ReconstructionMorphology.id)).where(
            ReconstructionMorphology.id == reconstruction_morphology_id
        ),
        user_context.project_id,
    )

    if db.execute(stmt).scalar_one() == 0:
        L.warning(
            "Block `MorphologyFeatureAnnotation` with entity inaccessible: {}",
            reconstruction_morphology_id,
        )
        raise HTTPException(
            status_code=404,
            detail=f"Cannot access entity {reconstruction_morphology_id}",
        )

    row = MorphologyFeatureAnnotation(reconstruction_morphology_id=reconstruction_morphology_id)

    for measurement in morphology_feature_annotation.measurements:
        db_measurement = MorphologyMeasurement()
        row.measurements.append(db_measurement)
        db_measurement.measurement_of = measurement.measurement_of

        for serie in measurement.measurement_serie:
            db_measurement.measurement_serie.append(
                MorphologyMeasurementSerieElement(**serie.model_dump())
            )

    db.add(row)
    db.commit()
    db.refresh(row)
    return row
