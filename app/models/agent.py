from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Root, TimestampMixin


class Agent(Root, TimestampMixin):
    __tablename__ = "agent"
    id: Mapped[int] = mapped_column(ForeignKey("root.id"), primary_key=True, index=True)
    pref_label = Column(String, unique=True, index=False, nullable=False)
    __mapper_args__ = {
        "polymorphic_identity": "agent",
    }


class Person(Agent):
    __tablename__ = "person"
    id: Mapped[int] = mapped_column(ForeignKey("agent.id"), primary_key=True)
    givenName = Column(String, unique=False, index=False, nullable=False)
    familyName = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {
        "polymorphic_identity": "person",
    }
    __table_args__ = (
        UniqueConstraint("givenName", "familyName", name="unique_person_name_1"),
    )


class Organization(Agent):
    __tablename__ = "organization"
    id: Mapped[int] = mapped_column(ForeignKey("agent.id"), primary_key=True)
    # what is the difference between name and label here ?
    alternative_name = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {
        "polymorphic_identity": "organization",
    }
