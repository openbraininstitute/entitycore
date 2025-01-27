from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.model import (
    MorphologyFeatureAnnotation,
    MorphologyMeasurement,
    MorphologyMeasurementSerieElement,
)

from app.dependencies.db import get_db

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
    db: Session = Depends(get_db),
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
def read_morphology_feature_annotations(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
):
    users = db.query(MorphologyFeatureAnnotation).offset(skip).limit(limit).all()
    return users
