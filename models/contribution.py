from models.base import TimestampMixin, Base
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

class Contribution(TimestampMixin, Base):
     __tablename__ = "contribution"
     id = Column(Integer, primary_key=True, index=True)
     agent_id = Column(Integer, ForeignKey("agent.id"), nullable=False)
     agent = relationship("Agent", uselist=False)