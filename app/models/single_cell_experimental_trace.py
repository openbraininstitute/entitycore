from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped

from app.models.base import (
    LicensedMixin,
    LocationMixin,
    SpeciesMixin,
)
from app.models.entity import Entity


class SingleCellExperimentalTrace(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "single_cell_experimental_trace"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(unique=False, index=True, nullable=False)
    description: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "single_cell_experimental_trace"}
