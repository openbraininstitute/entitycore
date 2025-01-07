from sqlalchemy import Column, ForeignKey, Integer, String

from app.models.base import DistributionMixin, LocationMixin, StringList
from app.models.entity import Entity
from sqlalchemy.orm import relationship, mapped_column


class SingleNeuronSimulation(DistributionMixin, LocationMixin, Entity):
    __tablename__ = "single_neuron_simulation"
    id = mapped_column(
        Integer,
        ForeignKey("entity.id"),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    description = Column(String, nullable=False, default="")
    name = Column(String, nullable=False, default="")
    seed = Column(Integer, nullable=False, default=-1)
    injectionLocation = Column(StringList, nullable=False, default="")
    recordingLocation = Column(StringList, nullable=False, default=[])
    # TODO: called used ?
    me_model_id = Column(Integer, ForeignKey("memodel.id"), nullable=False)
    me_model = relationship("MEModel", uselist=False, foreign_keys=[me_model_id])
    __mapper_args__ = {"polymorphic_identity": "single_neuron_simulation"}
