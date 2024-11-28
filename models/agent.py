from models.base import TimestampMixin, LegacyMixin, Base
from sqlalchemy import Column, Integer, String

class Agent(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "agent"
    id = Column(Integer, primary_key=True, index=True)

class Person(Agent):
    __tablename__ = "person"
    first_name = Column(String, unique=False, index=False, nullable=False)
    last_name = Column(String, unique=False, index=False, nullable=False)

class Organization(Agent):
    __tablename__ = "organization"
    name = Column(String, unique=False, index=False, nullable=False)