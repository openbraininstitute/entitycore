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
from sqlalchemy.orm import sessionmaker, relationship
from config import DATABASE_URI

engine = create_engine(DATABASE_URI, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TimestampMixin:
    creation_date = Column(DateTime, server_default=func.now())
    update_date = Column(DateTime, server_default=func.now(), onupdate=func.now())


class LegacyMixin:
    legacy_id = Column(String, unique=False, index=True, nullable=True)


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

class License(TimestampMixin, Base):
    __tablename__ = "license"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, unique=False, index=False, nullable=False)

Base.metadata.create_all(bind=engine)
