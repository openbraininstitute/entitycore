from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Contribution(TimestampMixin, Base):
    __tablename__ = "contribution"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agent.id"), nullable=False)
    agent = relationship("Agent", uselist=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"), nullable=False)
    role = relationship("Role", uselist=False)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id"), nullable=False)
    entity = relationship("Entity", uselist=False)
    __table_args__ = (
        UniqueConstraint(
            "entity_id", "role_id", "agent_id", name="unique_contribution_1"
        ),
    )
