from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column

from app.models.base import (
    Entity,
    LicensedMixin,
    LocationMixin,
    SpeciesMixin,
)


class SingleCellExperimentalTrace(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "single_cell_experimental_trace"
    id = mapped_column(Integer, ForeignKey("entity.id"), primary_key=True)
    name = Column(String, unique=False, index=True, nullable=False)
    description = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "single_cell_experimental_trace"}
