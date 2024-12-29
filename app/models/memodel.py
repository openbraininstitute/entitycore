
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column

from app.models.base import DistributionMixin, Entity, LocationMixin


class MEModel(DistributionMixin, LocationMixin, Entity):
    __tablename__ = "memodel"
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
    status = Column(String, nullable=False, default="")
    validated = Column(Boolean, nullable=False, default=False)
    
    
    __mapper_args__ = {"polymorphic_identity": "memodel"}


