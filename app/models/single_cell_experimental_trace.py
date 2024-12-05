from app.models.base import (
    LicensedMixin,
    LocationMixin,
    SpeciesMixin,
    Entity,
    Base,
    engine,
)
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import mapped_column


class SingleCellExperimentalTrace(
    LocationMixin, SpeciesMixin, LicensedMixin, Entity
):
    __tablename__ = "single_cell_experimental_trace"
    id = mapped_column(Integer, ForeignKey("entity.id"), primary_key=True)
    name = Column(String, unique=False, index=True, nullable=False)
    description = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "single_cell_experimental_trace"}

Base.metadata.create_all(bind=engine)
