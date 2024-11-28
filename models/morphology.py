from models.base import TimestampMixin, LegacyMixin, LicensedMixin, Base, engine
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship


class ReconstructionMorphology(LegacyMixin, TimestampMixin, LicensedMixin, Base):
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
    morphology_feature_annotation = relationship(
        "MorphologyFeatureAnnotation", uselist=False
    )


class MorphologyFeatureAnnotation(TimestampMixin, Base):
    __tablename__ = "morphology_feature_annotation"
    id = Column(Integer, primary_key=True, index=True)
    # name = Column(String, unique=True, index=True, nullable=False)
    # description = Column(String, unique=False, index=False, nullable=False)
    reconstruction_morphology_id = Column(
        Integer, ForeignKey("reconstruction_morphology.id"), nullable=False, unique=True
    )
    reconstruction_morphology = relationship(
        "ReconstructionMorphology",
        uselist=False,
        back_populates="morphology_feature_annotation",
    )
    measurements = relationship("MorphologyMeasurement", uselist=True)


class MorphologyMeasurement(Base):
    __tablename__ = "measurement"
    id = Column(Integer, primary_key=True, index=True)
    measurement_of = Column(String, unique=False, index=True, nullable=False)
    morphology_feature_annotation_id = Column(
        Integer, ForeignKey("morphology_feature_annotation.id"), nullable=False
    )
    measurement_serie = relationship("MorphologyMeasurementSerieElement", uselist=True)


class MorphologyMeasurementSerieElement(Base):
    __tablename__ = "measurement_serie_element"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=False, index=False, nullable=True)
    value = Column(Float, unique=False, index=False, nullable=True)
    measurement_id = Column(Integer, ForeignKey("measurement.id"), nullable=False)


Base.metadata.create_all(bind=engine)