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
from app.logger import L
from app.schemas.morphology import (
    MorphologyFeatureAnnotationCreate,
    MorphologyFeatureAnnotationRead,
)

router = APIRouter(
    prefix="/morphology_feature_annotation",
    tags=["brain_region"],
    responses={404: {"description": "Not found"}},
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


@router.get(
    "/{morphology_feature_annotation_id}",
    response_model=MorphologyFeatureAnnotationRead,
)
def read_morphology_feature_annotation_id(
    morphology_feature_annotation_id: int,
    project_context: VerifiedProjectContextHeader,
    db: SessionDep,
):
    row = (
        db.query(MorphologyFeatureAnnotation)
        .filter(
            MorphologyFeatureAnnotation.reconstruction_morphology_id
            == morphology_feature_annotation_id
        )
        .join(ReconstructionMorphology)
        .first()
    )

    if row is None:
        raise HTTPException(status_code=404, detail="Morphology annotation not found")

    if (
        not row.reconstruction_morphology.authorized_public
        and row.reconstruction_morphology.authorized_project_id != project_context.project_id
    ):
        L.warning("Attempting to get an annotation for an entity the user does not have access to")
        raise HTTPException(status_code=404, detail="Morphology annotation not found")

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
