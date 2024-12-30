from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column

from app.models.base import DistributionMixin, Entity, LocationMixin, SpeciesMixin

class EModel(DistributionMixin, SpeciesMixin, LocationMixin, Entity):
    __tablename__ = "emodel"
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
    # what is this
    eModel = Column(String, nullable=False, default="")
    # what is this
    eType = Column(String, nullable=False, default="")
    # what is this
    iteration = Column(String, nullable=False, default="")
    score= Column(Float, nullable=False, default=-1)
    seed = Column(Integer, nullable=False, default=-1)

    
    __mapper_args__ = {"polymorphic_identity": "emodel"}
