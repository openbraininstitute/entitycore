import sqlalchemy as sa
from fastapi import APIRouter, HTTPException

from app.db.auth import constrain_entity_query_to_project, constrain_to_accessible_entities
from app.db.model import (
    Entity,
    MorphologyFeatureAnnotation,
    MorphologyMeasurement,
    MorphologyMeasurementSerieElement,
    ReconstructionMorphology,
)
from app.dependencies import PaginationQuery
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.logger import L
from app.routers.types import ListResponse, PaginationResponse
from app.schemas.morphology import (
    MorphologyFeatureAnnotationCreate,
    MorphologyFeatureAnnotationRead,
)

router = APIRouter(
    prefix="/morphology-feature-annotation",
    tags=["morphology-feature-annotation"],
)


@router.get("/", response_model=ListResponse[MorphologyFeatureAnnotationRead])
def read_morphology_feature_annotations(
    db: SessionDep,
    project_context: VerifiedProjectContextHeader,
    pagination_request: PaginationQuery,
):
    query = constrain_to_accessible_entities(
        sa.select(MorphologyFeatureAnnotation).join(ReconstructionMorphology),
        project_context.project_id,
    )

    data = db.execute(
        query.offset(pagination_request.page * pagination_request.page_size).limit(
            pagination_request.page_size
        )
    ).scalars()

    total_items = db.execute(query.with_only_columns(sa.func.count())).scalar_one()

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


@router.get(
    "/{morphology_feature_annotation_id}",
    response_model=MorphologyFeatureAnnotationRead,
)
def read_morphology_feature_annotation_id(
    morphology_feature_annotation_id: int,
    project_context: VerifiedProjectContextHeader,
    db: SessionDep,
):
    with ensure_result(error_message="MorphologyFeatureAnnotation not found"):
        row = (
            db.query(MorphologyFeatureAnnotation)
            .filter(
                MorphologyFeatureAnnotation.reconstruction_morphology_id
                == morphology_feature_annotation_id
            )
            .join(ReconstructionMorphology)
            .one()
        )

    if (
        not row.reconstruction_morphology.authorized_public
        and row.reconstruction_morphology.authorized_project_id != project_context.project_id
    ):
        L.warning("Attempting to get an annotation for an entity the user does not have access to")
        raise HTTPException(status_code=404, detail="Morphology annotation not found")

    return row


@router.post("/", response_model=MorphologyFeatureAnnotationRead)
def create_morphology_feature_annotation(
    project_context: VerifiedProjectContextHeader,
    morphology_feature_annotation: MorphologyFeatureAnnotationCreate,
    db: SessionDep,
):
    reconstruction_morphology_id = morphology_feature_annotation.reconstruction_morphology_id

    if not constrain_entity_query_to_project(
        db.query(Entity).filter(
            Entity.id == morphology_feature_annotation.reconstruction_morphology_id
        ),
        project_context.project_id,
    ).first():
        L.warning(
            "Block `MorphologyFeatureAnnotation` with entity inaccessible: {}",
            reconstruction_morphology_id,
        )
        raise HTTPException(
            status_code=404,
            detail=f"Cannot access entity {reconstruction_morphology_id}",
        )

    db_morphology_feature_annotation = MorphologyFeatureAnnotation(
        reconstruction_morphology_id=reconstruction_morphology_id
    )

    for measurement in morphology_feature_annotation.measurements:
        db_measurement = MorphologyMeasurement()
        db_morphology_feature_annotation.measurements.append(db_measurement)
        db_measurement.measurement_of = measurement.measurement_of

        for serie in measurement.measurement_serie:
            db_measurement.measurement_serie.append(
                MorphologyMeasurementSerieElement(**serie.model_dump())
            )

    db.add(db_morphology_feature_annotation)
    db.commit()
    db.refresh(db_morphology_feature_annotation)
    return db_morphology_feature_annotation
