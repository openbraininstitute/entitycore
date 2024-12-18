from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    create_engine,
    DateTime,
    func,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, mapped_column
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.types import TypeDecorator, VARCHAR

from app.config import DATABASE_URI, DATABASE_CONNECT_ARGS

engine = create_engine(DATABASE_URI, connect_args=DATABASE_CONNECT_ARGS)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TimestampMixin:
    creation_date = Column(DateTime, server_default=func.now())
    update_date = Column(DateTime, server_default=func.now(), onupdate=func.now())


class StringList(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            return ",".join(value)

    def process_result_value(self, value, dialect):
        if value is not None:
            return value.split(",")

class LegacyMixin:
    legacy_id = Column(StringList, index=True, nullable=True)

class DistributionMixin:
    content_url = Column(String, unique=False, index=False, nullable=True)

class Root(LegacyMixin, Base):
    __tablename__ = "root"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "root", "polymorphic_on": type}


class Entity(TimestampMixin, Root):
    __tablename__ = "entity"
    id = mapped_column(Integer, ForeignKey("entity.id"), primary_key=True)
    # type = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {
        "polymorphic_identity": "entity",
        "inherit_condition": id == Root.id,
    }


class BrainLocation(Base):
    __tablename__ = "brain_location"
    id = Column(Integer, primary_key=True, index=True)
    x = Column(Float, unique=False, index=False, nullable=True)
    y = Column(Float, unique=False, index=False, nullable=True)
    z = Column(Float, unique=False, index=False, nullable=True)


class BrainRegion(TimestampMixin, Base):
    __tablename__ = "brain_region"
    id = Column(Integer, primary_key=True, index=True)
    ontology_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, unique=True, index=True, nullable=False)


class Species(TimestampMixin, Base):
    __tablename__ = "species"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    taxonomy_id = Column(String, unique=True, index=True, nullable=False)


class Strain(TimestampMixin, Base):
    __tablename__ = "strain"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    taxonomy_id = Column(String, unique=True, index=True, nullable=False)
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False)
    species = relationship("Species", uselist=False)


class Subject(TimestampMixin, Base):
    __tablename__ = "subject"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)


class License(TimestampMixin, LegacyMixin, Base):
    __tablename__ = "license"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, unique=False, index=False, nullable=False)
    label = Column(String, unique=False, index=False, nullable=False)


class LicensedMixin:
    license_id = Column(Integer, ForeignKey("license.id"), nullable=True)

    @declared_attr
    def license(cls):
        return relationship("License", uselist=False)


class LocationMixin:
    brain_location_id = Column(Integer, ForeignKey("brain_location.id"), nullable=True)

    @declared_attr
    def brain_location(cls):
        return relationship("BrainLocation", uselist=False)

    brain_region_id = Column(Integer, ForeignKey("brain_region.id"), nullable=False)

    @declared_attr
    def brain_region(cls):
        return relationship("BrainRegion", uselist=False)


class SpeciesMixin:
    species_id = Column(Integer, ForeignKey("species.id"), nullable=False)

    @declared_attr
    def species(cls):
        return relationship("Species", uselist=False)

    strain_id = Column(Integer, ForeignKey("strain.id"), nullable=True)

    @declared_attr
    def strain(cls):
        return relationship("Strain", uselist=False)


Base.metadata.create_all(bind=engine)
