
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import mapped_column, relationship

from app.models.base import Root, TimestampMixin


class Entity(TimestampMixin, Root):
    __tablename__ = "entity"
    id = mapped_column(Integer, ForeignKey("root.id"), primary_key=True)
    # type = Column(String, unique=False, index=False, nullable=False)
    annotations = relationship("Annotation", back_populates="entity")
    #TODO: keep the _ ? put on agent ?
    createdBy = relationship("Agent", uselist=False, foreign_keys="Entity.createdBy_id")
    #TODO: move to mandatory
    createdBy_id = Column(Integer, ForeignKey("agent.id"), nullable=True)
    updatedBy = relationship("Agent", uselist=False, foreign_keys="Entity.updatedBy_id")
    #TODO: move to mandatory
    updatedBy_id = Column(Integer, ForeignKey("agent.id"), nullable=True)
    __mapper_args__ = {
        "polymorphic_identity": "entity",
        "inherit_condition": id == Root.id,
    }
