from models.base import (
    TimestampMixin,
    LicensedMixin,
    LocationMixin,
    SpeciesMixin,
    Entity,
    Base,
    engine,
)
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import mapped_column


class ExperimentalNeuronDensity(
    LocationMixin, SpeciesMixin, LicensedMixin, Entity
):
    __tablename__ = "experimental_neuron_density"
    id = mapped_column(Integer, ForeignKey("entity.id"), primary_key=True)
    name = Column(String, unique=False, index=True, nullable=False)
    description = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "experimental_neuron_density"}


Base.metadata.create_all(bind=engine)
