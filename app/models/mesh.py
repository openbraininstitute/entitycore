from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped

from app.models.base import DistributionMixin
from app.models.entity import Entity


class Mesh(DistributionMixin, Entity):
    __tablename__ = "mesh"
    id: Mapped[int] = mapped_column(
        ForeignKey("entity.id"),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    brain_region_id: Mapped[int] = mapped_column(
        ForeignKey("brain_region.id"), nullable=False
    )
    brain_region = relationship("BrainRegion", uselist=False)
    __mapper_args__ = {"polymorphic_identity": "mesh"}
