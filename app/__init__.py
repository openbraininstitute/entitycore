from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.models.base import BrainRegion, License, Species, Strain
from app.models.morphology import (
    MorphologyFeatureAnnotation,
    MorphologyMeasurement,
    MorphologyMeasurementSerieElement,
)
from app.routers import (
    contribution,
    experimental_bouton_density,
    experimental_neuron_density,
    experimental_synapses_per_connection,
    morphology,
    organization,
    person,
    role,
)
from app.routers.legacy import _search, files, resources, sbo
from app.schemas.base import (
    BrainRegionCreate,
    BrainRegionRead,
    LicenseCreate,
    LicenseRead,
    SpeciesCreate,
    StrainCreate,
)
from app.schemas.morphology import (
    MorphologyFeatureAnnotationCreate,
    MorphologyFeatureAnnotationRead,
    SpeciesRead,
    StrainRead,
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(morphology.router)
app.include_router(person.router)
app.include_router(organization.router)
app.include_router(contribution.router)
app.include_router(role.router)
app.include_router(experimental_bouton_density.router)
app.include_router(experimental_neuron_density.router)
app.include_router(experimental_synapses_per_connection.router)
# legacy routes
app.include_router(_search.router)
app.include_router(sbo.router)
app.include_router(resources.router)
app.include_router(files.router)


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
                MorphologyMeasurementSerieElement(**serie.model_dump())
            )

    db.add(db_morphology_feature_annotation)
    db.commit()
    db.refresh(db_morphology_feature_annotation)
    return db_morphology_feature_annotation


@app.get(
    "/morphology_feature_annotation/",
    response_model=list[MorphologyFeatureAnnotationCreate],
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


@app.get("/license/", response_model=list[LicenseRead])
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
    db_license = License(
        name=license.name, description=license.description, label=license.label
    )
    db.add(db_license)
    db.commit()
    db.refresh(db_license)
    return db_license
