from sqlalchemy import ForeignKey, Column
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import mapped_column, relationship, Mapped

from app.models.base import (
    Base,
    LicensedMixin,
    LocationMixin,
    SpeciesMixin,
    TimestampMixin,
)
from app.models.entity import Entity


class ReconstructionMorphology(LicensedMixin, LocationMixin, SpeciesMixin, Entity):
    __tablename__ = "reconstruction_morphology"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    description: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    # name is not unique
    name: Mapped[str] = mapped_column(unique=False, index=True, nullable=False)
    morphology_description_vector = Column(TSVECTOR, nullable=True)
    morphology_feature_annotation = relationship(
        "MorphologyFeatureAnnotation", uselist=False
    )
    __mapper_args__ = {"polymorphic_identity": "reconstruction_morphology"}


class MorphologyFeatureAnnotation(TimestampMixin, Base):
    __tablename__ = "morphology_feature_annotation"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # name = mapped_column(String, unique=True, index=True, nullable=False)
    # description = mapped_column(String, unique=False, index=False, nullable=False)
    reconstruction_morphology_id: Mapped[int] = mapped_column(
        ForeignKey("reconstruction_morphology.id"), nullable=False, unique=True
    )
    reconstruction_morphology = relationship(
        "ReconstructionMorphology",
        uselist=False,
        back_populates="morphology_feature_annotation",
    )
    measurements = relationship("MorphologyMeasurement", uselist=True)


class MorphologyMeasurement(Base):
    __tablename__ = "measurement"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    measurement_of: Mapped[str] = mapped_column(
        unique=False, index=True, nullable=False
    )
    morphology_feature_annotation_id: Mapped[int] = mapped_column(
        ForeignKey("morphology_feature_annotation.id"), nullable=False
    )
    measurement_serie = relationship("MorphologyMeasurementSerieElement", uselist=True)


class MorphologyMeasurementSerieElement(Base):
    __tablename__ = "measurement_serie_element"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=False, index=False, nullable=True)
    value: Mapped[float] = mapped_column(unique=False, index=False, nullable=True)
    measurement_id: Mapped[int] = mapped_column(
        ForeignKey("measurement.id"), nullable=False
    )
