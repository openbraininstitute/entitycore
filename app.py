from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import routers.morphology
import routers.agent
from typing import List
from dependencies.db import get_db
from schemas.morphology import (
    MorphologyFeatureAnnotationCreate,
    MorphologyFeatureAnnotationRead,
    SpeciesRead,
    StrainRead,
)
from schemas.base import (
    BrainRegionRead,
    BrainRegionCreate,
    SpeciesCreate,
    StrainCreate,
    LicenseRead,
    LicenseCreate,
)
from models.morphology import (
    MorphologyFeatureAnnotation,
    MorphologyMeasurement,
    MorphologyMeasurementSerieElement,
)
from models.base import Species, License, BrainRegion, Strain

app = FastAPI()
app.include_router(routers.morphology.router)
app.include_router(routers.agent.router)



@app.post("/species/", response_model=SpeciesRead)
def create_species(species: SpeciesCreate, db: Session = Depends(get_db)):
    db_species = Species(name=species.name, taxonomy_id=species.taxonomy_id)
    db.add(db_species)
    db.commit()
    db.refresh(db_species)
    return db_species


@app.post("/strain/", response_model=StrainRead)
def create_strain(strain: StrainCreate, db: Session = Depends(get_db)):
    db_strain = Strain(
        name=strain.name, taxonomy_id=strain.taxonomy_id, species_id=strain.species_id
    )
    db.add(db_strain)
    db.commit()
    db.refresh(db_strain)
    return db_strain


@app.post(
    "/morphology_feature_annotation/", response_model=MorphologyFeatureAnnotationRead
)
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
                MorphologyMeasurementSerieElement(**serie.dict())
            )

    db.add(db_morphology_feature_annotation)
    db.commit()
    db.refresh(db_morphology_feature_annotation)
    return db_morphology_feature_annotation


@app.get(
    "/morphology_feature_annotation/",
    response_model=List[MorphologyFeatureAnnotationCreate],
)
async def read_morphology_feature_annotations(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_db)
):
    users = db.query(MorphologyFeatureAnnotation).offset(skip).limit(limit).all()
    return users


@app.post("/brain_region/", response_model=BrainRegionRead)
def create_brain_region(brain_region: BrainRegionCreate, db: Session = Depends(get_db)):
    db_brain_region = BrainRegion(
        ontology_id=brain_region.ontology_id, name=brain_region.name
    )
    db.add(db_brain_region)
    db.commit()
    db.refresh(db_brain_region)
    return db_brain_region


@app.get("/license/", response_model=List[LicenseRead])
async def read_licenses(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(License).offset(skip).limit(limit).all()
    return users


@app.get("/license/{license_id}", response_model=LicenseRead)
async def read_license(license_id: int, db: Session = Depends(get_db)):
    license = db.query(License).filter(License.id == license_id).first()
    if license is None:
        raise HTTPException(status_code=404, detail="License not found")
    return license


@app.post("/license/", response_model=LicenseRead)
def create_license(license: LicenseCreate, db: Session = Depends(get_db)):
    db_license = License(name=license.name, description=license.description)
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    return db_license
