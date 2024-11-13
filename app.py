from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import model
from datetime import datetime
app = FastAPI()

# Dependency to get the database session
def get_db():
    db = model.SessionLocal()
    try:
        yield db
    finally:
        db.close()

class BrainLocationCreate(BaseModel):
    x: float
    y: float
    z: float
    class Config:
        orm_mode = True

class BrainRegionCreate(BaseModel):
    ontology_id: str
    name: str 
    class Config:
        orm_mode = True

class StrainCreate(BaseModel):
    Name: str
    taxonomy_id: str
    species_id: int
    class Config:
        orm_mode = True

class StrainRead(StrainCreate):
    id: int
    creation_date: datetime
    update_date: datetime
    def dict(self, **kwargs):
        result = super().dict(**kwargs)
        result['creation_date'] = result['creation_date'].isoformat() if result['creation_date'] else None
        result['update_date'] = result['update_date'].isoformat() if result['update_date'] else None
        return result

class SpeciesCreate(BaseModel):
    Name: str
    taxonomy_id: str
    class Config:
        orm_mode = True

class SpeciesRead(SpeciesCreate):
    id: int
    creation_date: datetime
    update_date: datetime
    def dict(self, **kwargs):
        result = super().dict(**kwargs)
        result['creation_date'] = result['creation_date'].isoformat() if result['creation_date'] else None
        result['update_date'] = result['update_date'].isoformat() if result['update_date'] else None
        return result
    
        
class ReconstructionMorphologyBase(BaseModel):
    name: str
    description: str
    brain_location: BrainLocationCreate
    class Config:
        orm_mode = True

class ReconstructionMorphologyCreate(ReconstructionMorphologyBase):
    species_id: int
    strain_id: int
    brain_region_id: BrainRegionCreate

class ReconstructionMorphologyRead(ReconstructionMorphologyBase):
    id: int
    creation_date: datetime 
    update_date: datetime
    species: SpeciesCreate
    strain: StrainCreate
    brain_region: BrainRegionCreate
    def dict(self, **kwargs):
        result = super().dict(**kwargs)
        result['creation_date'] = result['creation_date'].isoformat() if result['creation_date'] else None
        result['update_date'] = result['update_date'].isoformat() if result['update_date'] else None
        return result

class MeasurementCreate(BaseModel):
    id: int
    value: float
    measurement_of: str
    name: str
    class Config:
        orm_mode = True

class MorphologyFeatureAnnotationCreate(BaseModel):
    reconstruction_morphology_id: int
    measurements: List[MeasurementCreate]
    class Config:
        orm_mode = True 

@app.post("/reconstruction_morphology/", response_model=ReconstructionMorphologyRead)
def create_reconstruction_morphology(recontruction: ReconstructionMorphologyCreate, db: Session = Depends(get_db)):
    db_reconstruction_morphology = model.ReconstructionMorphology(name=recontruction.name,
                                            description=recontruction.description,
                                            brain_location_id=model.BrainLocation(**recontruction.brain_location.dict()),
                                            brain_region_id=recontruction.brain_region_id,
                                            species_id=recontruction.species_id,
                                            strain_id=recontruction.strain_id)
    db.add(db_reconstruction_morphology)
    db.commit()
    db.refresh(db_reconstruction_morphology)
    print(db_reconstruction_morphology)
    return db_reconstruction_morphology


@app.get("/reconstruction_morphology/", response_model=List[ReconstructionMorphologyRead])
async def read_reconstruction_morphologies(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(model.ReconstructionMorphology).offset(skip).limit(limit).all()
    return users

@app.get("/reconstruction_morphology/{rm_id}", response_model=ReconstructionMorphologyRead)
async def read_reconstruction_morphology(rm_id: int, db: Session = Depends(get_db)):
    user = db.query(model.ReconstructionMorphology).filter(model.ReconstructionMorphology.id == rm_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="ReconstructionMorphology not found")
    return user

@app.post("/species/", response_model=SpeciesRead)
def create_species(species: SpeciesCreate, db: Session = Depends(get_db)):
    db_species = model.Species(Name=species.Name, taxonomy_id=species.taxonomy_id)
    db.add(db_species)
    db.commit()
    db.refresh(db_species)
    return db_species

@app.post("/strain/", response_model=StrainRead)
def create_strain(strain: StrainCreate, db: Session = Depends(get_db)):
    db_strain = model.Strain(Name=strain.Name, taxonomy_id=strain.taxonomy_id, species_id=strain.species_id)
    db.add(db_strain)
    db.commit()
    db.refresh(db_strain)
    return db_strain

@app.post("/morphology_feature_annotation/", response_model=MorphologyFeatureAnnotationCreate)
def create_morphology_feature_annotation(morphology_feature_annotation: MorphologyFeatureAnnotationCreate, db: Session = Depends(get_db)):
    db_morphology_feature_annotation = model.MorphologyFeatureAnnotation(reconstruction_morphology_id=morphology_feature_annotation.reconstruction_morphology_id)
    db_morphology_feature_annotation.measurements = [model.MorphologyMeasurement(**measurement.dict()) for measurement in morphology_feature_annotation.measurements]
    db.add(db_morphology_feature_annotation)
    db.commit()
    db.refresh(db_morphology_feature_annotation)
    return db_morphology_feature_annotation

@app.get("/morphology_feature_annotation/", response_model=List[MorphologyFeatureAnnotationCreate])
async def read_morphology_feature_annotations(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(model.MorphologyFeatureAnnotation).offset(skip).limit(limit).all()
    return users
