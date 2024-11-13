from sqlalchemy import Column, Integer,Float, String, create_engine, DateTime, func, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TimestampMixin:
    creation_date = Column(DateTime, server_default=func.now())
    update_date = Column(DateTime, server_default=func.now(), onupdate=func.now())

class BrainLocation(Base):
    __tablename__ = "brain_location"
    id = Column(Integer, primary_key=True, index=True)
    x = Column(Float, unique=False, index=False, nullable=True)
    y = Column(Float, unique=False, index=False, nullable=True)
    z = Column(Float, unique=False, index=False, nullable=True)

class BrainRegion(TimestampMixin, Base):
    __tablename__ = "brain_region"
    id = Column(Integer, primary_key=True, index=True)
    ontology_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, unique=True, index=True, nullable=False)

class ReconstructionMorphology(TimestampMixin, Base):
    __tablename__ = "reconstruction_morphology"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, unique=False, index=False, nullable=False)
    name = Column(String, unique=False, index=True, nullable=True)
    brain_location_id = Column(Integer, ForeignKey("brain_location.id"), nullable=True)
    brain_location = relationship("BrainLocation", uselist=False)
    brain_region_id = Column(Integer, ForeignKey("brain_region.id"), nullable=True)
    brain_region = relationship("BrainRegion", uselist=False)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False)
    species = relationship("Species", uselist=False)
    strain_id = Column(Integer, ForeignKey("strain.id"), nullable=True)
    strain = relationship("Strain", uselist=False)
    morphology_feature_annotation = relationship("MorphologyFeatureAnnotation", uselist=False)

class Species(TimestampMixin, Base):
    __tablename__ = "species"
    id = Column(Integer, primary_key=True, index=True)
    Name = Column(String, unique=True, index=True, nullable=False)
    taxonomy_id = Column(String, unique=True, index=True, nullable=False)

class Strain(TimestampMixin, Base):
    __tablename__ = "strain"
    id = Column(Integer, primary_key=True, index=True)
    Name = Column(String, unique=True, index=True, nullable=False)
    taxonomy_id = Column(String, unique=True, index=True, nullable=False)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False)
    species = relationship("Species", uselist=False)

class Subject(TimestampMixin, Base):
    __tablename__ = "subject"
    id = Column(Integer, primary_key=True, index=True)
    Name = Column(String, unique=True, index=True, nullable=False)
                  
class MorphologyFeatureAnnotation(TimestampMixin, Base):
    __tablename__ = "morphology_feature_annotation"
    id = Column(Integer, primary_key=True, index=True)
    # name = Column(String, unique=True, index=True, nullable=False)
    # description = Column(String, unique=False, index=False, nullable=False)
    reconstruction_morphology_id = Column(Integer, ForeignKey("reconstruction_morphology.id"), nullable=False)
    reconstruction_morphology = relationship("ReconstructionMorphology", uselist=False, back_populates="morphology_feature_annotation")
    measurements = relationship("MorphologyMeasurement", uselist=True)

class MorphologyMeasurement(Base):
    __tablename__ = "measurement"
    id = Column(Integer, primary_key=True, index=True)
    measurement_of = Column(String, unique=False, index=True, nullable=False)
    name = Column(String, unique=False, index=False, nullable=True)
    value = Column(Float, unique=False, index=False, nullable=True)
    morphology_feature_annotation_id = Column(Integer, ForeignKey("morphology_feature_annotation.id"), nullable=False)


Base.metadata.create_all(bind=engine)
