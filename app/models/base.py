from datetime import datetime
from typing import Annotated, ClassVar

from sqlalchemy import (
    DateTime,
    ForeignKey,
    create_engine,
    func,
    or_,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
    relationship,
    sessionmaker,
)
from sqlalchemy.types import VARCHAR, TypeDecorator

from app.config import DATABASE_CONNECT_ARGS, DATABASE_URI

engine = create_engine(DATABASE_URI, connect_args=DATABASE_CONNECT_ARGS)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class StringListType(TypeDecorator):
    impl = VARCHAR
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return ",".join(value)

    def process_result_value(self, value, dialect):
        if value is not None:
            return value.split(",")

    @staticmethod
    def is_equal(column, value):
        use_func = func.instr
        if engine.dialect.name == "postgresql":
            use_func = func.strpos
        return use_func(column, value) > 0

    @staticmethod
    def in_(column, values):
        return or_(*[StringList.is_equal(column, value) for value in values])


StringList = Annotated[StringListType, "StringList"]


class Base(DeclarativeBase):
    type_annotation_map: ClassVar[dict] = {
        datetime: DateTime(timezone=True),
        StringList: StringListType,
    }


class TimestampMixin:
    creation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    update_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LegacyMixin:
    legacy_id: Mapped[StringList] = mapped_column(index=True, nullable=True)


class DistributionMixin:
    content_url: Mapped[str] = mapped_column(unique=False, index=False, nullable=True)


class Root(LegacyMixin, Base):
    __tablename__ = "root"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    type: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {
        "polymorphic_identity": "root",
        "polymorphic_on": type,
    }


class BrainLocation(Base):
    __tablename__ = "brain_location"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    x: Mapped[float] = mapped_column(unique=False, index=False, nullable=True)
    y: Mapped[float] = mapped_column(unique=False, index=False, nullable=True)
    z: Mapped[float] = mapped_column(unique=False, index=False, nullable=True)


class BrainRegion(TimestampMixin, Base):
    __tablename__ = "brain_region"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ontology_id: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)


class Species(TimestampMixin, Base):
    __tablename__ = "species"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    taxonomy_id: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)


class Strain(TimestampMixin, Base):
    __tablename__ = "strain"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    taxonomy_id: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id"), nullable=False)
    species = relationship("Species", uselist=False)


class Subject(TimestampMixin, Base):
    __tablename__ = "subject"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)


class License(TimestampMixin, LegacyMixin, Base):
    __tablename__ = "license"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    label: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)


class LicensedMixin:
    license_id: Mapped[int] = mapped_column(ForeignKey("license.id"), nullable=True)

    @declared_attr
    def license(cls):
        return relationship("License", uselist=False)


class LocationMixin:
    brain_location_id: Mapped[int] = mapped_column(
        ForeignKey("brain_location.id"), nullable=True
    )

    @declared_attr
    def brain_location(cls):
        return relationship("BrainLocation", uselist=False)

    brain_region_id: Mapped[int] = mapped_column(
        ForeignKey("brain_region.id"), nullable=False
    )

    @declared_attr
    def brain_region(cls):
        return relationship("BrainRegion", uselist=False)


class SpeciesMixin:
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id"), nullable=False)

    @declared_attr
    def species(cls):
        return relationship("Species", uselist=False)

    strain_id = mapped_column(ForeignKey("strain.id"), nullable=True)

    @declared_attr
    def strain(cls):
        return relationship("Strain", uselist=False)
