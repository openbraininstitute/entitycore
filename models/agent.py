from models.base import TimestampMixin, LegacyMixin, Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import mapped_column


class Agent(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "agent"
    id = mapped_column(Integer, primary_key=True, index=True)
    type = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "agent", "polymorphic_on": type}


class Person(Agent):
    __tablename__ = "person"
    id = mapped_column(Integer, ForeignKey("agent.id"), primary_key=True)
    first_name = Column(String, unique=False, index=False, nullable=False)
    last_name = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "person"}


class Organization(Agent):
    __tablename__ = "organization"
    id = mapped_column(Integer, ForeignKey("agent.id"), primary_key=True)
    name = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "organization"}
