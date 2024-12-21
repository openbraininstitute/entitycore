from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import mapped_column, relationship

from app.models.base import Base, DistributionMixin, Entity, engine


class Mesh(DistributionMixin, Entity):
    __tablename__ = "mesh"
    id = mapped_column(
        Integer,
        ForeignKey("entity.id"),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    brain_region_id = Column(Integer, ForeignKey("brain_region.id"), nullable=False)
    brain_region = relationship("BrainRegion", uselist=False)
    __mapper_args__ = {"polymorphic_identity": "mesh"}


Base.metadata.create_all(bind=engine)
