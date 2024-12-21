from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Contribution(TimestampMixin, Base):
    __tablename__ = "contribution"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agent.id"), nullable=False)
    agent = relationship("Agent", uselist=False)
    role_id = Column(Integer, ForeignKey("role.id"), nullable=False)
    role = relationship("Role", uselist=False)
    entity_id = Column(Integer, ForeignKey("entity.id"), nullable=False)
    entity = relationship("Entity", uselist=False)
    __table_args__ = (
        UniqueConstraint(
            "entity_id", "role_id", "agent_id", name="unique_contribution_1"
        ),
    )
