from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped

from app.models.base import (
    LicensedMixin,
    LocationMixin,
    SpeciesMixin,
)
from app.models.entity import Entity


class ExperimentalNeuronDensity(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "experimental_neuron_density"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(unique=False, index=True, nullable=False)
    description: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "experimental_neuron_density"}


class ExperimentalBoutonDensity(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "experimental_bouton_density"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(unique=False, index=True, nullable=False)
    description: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "experimental_bouton_density"}


class ExperimentalSynapsesPerConnection(
    LocationMixin, SpeciesMixin, LicensedMixin, Entity
):
    __tablename__ = "experimental_synapses_per_connection"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(unique=False, index=True, nullable=False)
    description: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "experimental_synapses_per_connection"}
