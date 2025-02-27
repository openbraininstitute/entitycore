from fastapi import APIRouter, HTTPException

from app.db.auth import constrain_entity_query_to_project, constrain_to_accessible_entities
from app.db.model import (
    Entity,
    MorphologyFeatureAnnotation,
    MorphologyMeasurement,
    MorphologyMeasurementSerieElement,
    ReconstructionMorphology,
)
from app.dependencies.auth import VerifiedProjectContextHeader
from app.dependencies.db import SessionDep
from app.errors import ensure_result
from app.logger import L
from app.schemas.morphology import (
    MorphologyFeatureAnnotationCreate,
    MorphologyFeatureAnnotationRead,
)

router = APIRouter(
    prefix="/morphology-feature-annotation",
    tags=["morphology-feature-annotation"],
)


@router.get("/", response_model=list[MorphologyFeatureAnnotationRead])
def read_morphology_feature_annotations(
    project_context: VerifiedProjectContextHeader, db: SessionDep, skip: int = 0, limit: int = 10
):
    return (
        constrain_to_accessible_entities(
            db.query(MorphologyFeatureAnnotation).join(ReconstructionMorphology),
            project_context.project_id,
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{id_}", response_model=MorphologyFeatureAnnotationRead)
def read_morphology_feature_annotation_id(
    id_: int,
    project_context: VerifiedProjectContextHeader,
    db: SessionDep,
):
    with ensure_result(error_message="MorphologyFeatureAnnotation not found"):
        row = constrain_to_accessible_entities(
            db.query(MorphologyFeatureAnnotation)
            .filter(MorphologyFeatureAnnotation.reconstruction_morphology_id == id_)
            .join(ReconstructionMorphology),
            project_context.project_id,
        ).one()

    return MorphologyFeatureAnnotationRead.model_validate(row)


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
