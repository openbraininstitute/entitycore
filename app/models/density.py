from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column

from app.models.base import (
    Base,
    Entity,
    LicensedMixin,
    LocationMixin,
    SpeciesMixin,
    engine,
)


class ExperimentalNeuronDensity(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "experimental_neuron_density"
    id = mapped_column(Integer, ForeignKey("entity.id"), primary_key=True)
    name = Column(String, unique=False, index=True, nullable=False)
    description = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "experimental_neuron_density"}


class ExperimentalBoutonDensity(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "experimental_bouton_density"
    id = mapped_column(Integer, ForeignKey("entity.id"), primary_key=True)
    name = Column(String, unique=False, index=True, nullable=False)
    description = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "experimental_bouton_density"}


class ExperimentalSynapsesPerConnection(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "experimental_synapses_per_connection"
    id = mapped_column(Integer, ForeignKey("entity.id"), primary_key=True)
    name = Column(String, unique=False, index=True, nullable=False)
    description = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "experimental_synapses_per_connection"}


Base.metadata.create_all(bind=engine)
