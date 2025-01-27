from fastapi import APIRouter

from app.db.model import (
    MorphologyFeatureAnnotation,
    MorphologyMeasurement,
    MorphologyMeasurementSerieElement,
)
from app.dependencies.db import SessionDep
from app.schemas.morphology import (
    MorphologyFeatureAnnotationCreate,
    MorphologyFeatureAnnotationRead,
)

router = APIRouter(
    prefix="/morphology_feature_annotation",
    tags=["brain_region"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=MorphologyFeatureAnnotationRead)
def create_morphology_feature_annotation(
    morphology_feature_annotation: MorphologyFeatureAnnotationCreate,
    db: SessionDep,
):
    db_morphology_feature_annotation = MorphologyFeatureAnnotation(
        reconstruction_morphology_id=morphology_feature_annotation.reconstruction_morphology_id
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


@router.get("/", response_model=list[MorphologyFeatureAnnotationCreate])
def read_morphology_feature_annotations(db: SessionDep, skip: int = 0, limit: int = 10):
    return db.query(MorphologyFeatureAnnotation).offset(skip).limit(limit).all()
