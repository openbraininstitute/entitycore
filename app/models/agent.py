from app.models.base import TimestampMixin, Base, engine, Root
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import mapped_column


class Agent(Root, TimestampMixin):
    __tablename__ = "agent"
    id = mapped_column(Integer, ForeignKey("root.id"), primary_key=True, index=True)
    __mapper_args__ = {
        "polymorphic_identity": "agent",
        "inherit_condition": id == Root.id,
    }


class Person(Agent):
    __tablename__ = "person"
    id = mapped_column(Integer, ForeignKey("agent.id"), primary_key=True)
    givenName = Column(String, unique=False, index=False, nullable=False)
    familyName = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {
        "polymorphic_identity": "person",
        "inherit_condition": id == Agent.id,
    }
    __table_args__ = (
        UniqueConstraint("givenName", "familyName", name="unique_person_name_1"),
    )


class Organization(Agent):
    __tablename__ = "organization"
    id = mapped_column(Integer, ForeignKey("agent.id"), primary_key=True)
    name = Column(String, unique=True, index=False, nullable=False)
    # what is the difference between name and label here ?
    label = Column(String, unique=False, index=False, nullable=True)
    alternative_name = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {
        "polymorphic_identity": "organization",
        "inherit_condition": id == Agent.id,
    }


Base.metadata.create_all(bind=engine)
