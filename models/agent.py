from models.base import TimestampMixin, LegacyMixin, Base, engine
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import mapped_column
from sqlalchemy.types import TypeDecorator, VARCHAR

class StringList(TypeDecorator): 
    impl = VARCHAR
    def process_bind_param(self, value, dialect):
         if value is not None: return ','.join(value)
    def process_result_value(self, value, dialect):
        if value is not None: return value.split(',')

class Agent(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "agent"
    id = mapped_column(Integer, primary_key=True, index=True)
    type = Column(String, unique=False, index=False, nullable=False)
    legacy_id = Column(StringList)
    __mapper_args__ = {"polymorphic_identity": "agent", "polymorphic_on": type}


class Person(Agent):
    __tablename__ = "person"
    id = mapped_column(Integer, ForeignKey("agent.id"), primary_key=True)
    first_name = Column(String, unique=False, index=False, nullable=False)
    last_name = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "person"}
    __table_args__ = (UniqueConstraint('first_name', 'last_name', name='unique_person_name_1'),)


class Organization(Agent):
    __tablename__ = "organization"
    id = mapped_column(Integer, ForeignKey("agent.id"), primary_key=True)
    name = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "organization"}

Base.metadata.create_all(bind=engine)
