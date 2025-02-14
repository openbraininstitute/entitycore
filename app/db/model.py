from datetime import datetime
from typing import ClassVar
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    MetaData,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column, relationship

from app.db.types import StringList, StringListType


class Base(DeclarativeBase):
    type_annotation_map: ClassVar[dict] = {
        datetime: DateTime(timezone=True),
        StringList: StringListType,
    }
    # See https://alembic.sqlalchemy.org/en/latest/naming.html
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class TimestampMixin:
    creation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
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
    __mapper_args__ = {  # noqa: RUF012
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

    # See https://github.com/openbraininstitute/core-web-app/blob/cd89893db3fe08a1d2e5ba90235ef6d8c7be6484/src/types/ontologies.ts#L7
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    acronym: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    children: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), nullable=True)


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
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id"), index=True, nullable=False)
    species = relationship("Species", uselist=False)

    __table_args__ = (
        # needed for the composite foreign key in SpeciesMixin
        UniqueConstraint("id", "species_id", name="uq_strain_id_species_id"),
    )


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
    license_id: Mapped[int] = mapped_column(ForeignKey("license.id"), index=True, nullable=True)

    @declared_attr
    @classmethod
    def license(cls):
        return relationship("License", uselist=False)


class LocationMixin:
    brain_location_id: Mapped[int] = mapped_column(
        ForeignKey("brain_location.id"), index=True, nullable=True
    )

    @declared_attr
    @classmethod
    def brain_location(cls):
        return relationship("BrainLocation", uselist=False)

    brain_region_id: Mapped[int] = mapped_column(
        ForeignKey("brain_region.id"), index=True, nullable=False
    )

    @declared_attr
    @classmethod
    def brain_region(cls):
        return relationship("BrainRegion", uselist=False)


class SpeciesMixin:
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id"), index=True, nullable=False)

    @declared_attr
    @classmethod
    def species(cls):
        return relationship("Species", uselist=False)

    # not defined as ForeignKey to avoid ambiguities with the composite foreign key
    strain_id: Mapped[int | None] = mapped_column(index=True, nullable=True)

    @declared_attr
    @classmethod
    def strain(cls):
        # viewonly is needed to prevent copying strain.species_id to species_id
        # primaryjoin is needed to ignore species_id from the ForeignKeyConstraint
        return relationship(
            "Strain", uselist=False, viewonly=True, primaryjoin=cls.strain_id == Strain.id
        )

    @declared_attr.directive
    @classmethod
    def __table_args__(cls):  # noqa: D105, PLW3201
        # ensure that species_id and strain.species_id are have the same value
        return (
            ForeignKeyConstraint(
                ["strain_id", "species_id"],
                ["strain.id", "strain.species_id"],
                name=f"fk_{cls.__tablename__}_strain_id_species_id",
            ),
        )


class Agent(Root, TimestampMixin):
    __tablename__ = "agent"
    id: Mapped[int] = mapped_column(ForeignKey("root.id"), primary_key=True, index=True)
    pref_label: Mapped[str] = mapped_column(unique=True, index=False, nullable=False)
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "agent",
    }


class Person(Agent):
    __tablename__ = "person"
    id: Mapped[int] = mapped_column(ForeignKey("agent.id"), primary_key=True)
    givenName: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    familyName: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "person",
    }
    __table_args__ = (UniqueConstraint("givenName", "familyName", name="unique_person_name_1"),)


class Organization(Agent):
    __tablename__ = "organization"
    id: Mapped[int] = mapped_column(ForeignKey("agent.id"), primary_key=True)
    # what is the difference between name and label here ?
    alternative_name: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "organization",
    }


class AnnotationBody(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "annotation_body"
    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, nullable=False, autoincrement=True
    )
    type: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "annotation_body",
        "polymorphic_on": type,
    }


class MTypeAnnotationBody(AnnotationBody):
    __tablename__ = "mtype_annotation_body"
    id: Mapped[int] = mapped_column(
        ForeignKey("annotation_body.id"),
        primary_key=True,
        index=True,
        nullable=False,
        autoincrement=True,
    )
    pref_label: Mapped[str] = mapped_column(unique=True, nullable=False)
    # difficult to believe this can be null
    definition: Mapped[str] = mapped_column(unique=False, nullable=True)
    alt_label: Mapped[str] = mapped_column(unique=False, nullable=True)
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "mtype_annotation_body",
    }


class ETypeAnnotationBody(AnnotationBody):
    __tablename__ = "etype_annotation_body"
    id: Mapped[int] = mapped_column(
        ForeignKey("annotation_body.id"),
        primary_key=True,
        index=True,
        nullable=False,
        autoincrement=True,
    )
    pref_label: Mapped[str] = mapped_column(unique=True, nullable=False)
    definition: Mapped[str] = mapped_column(unique=False, nullable=True)
    alt_label: Mapped[str] = mapped_column(unique=False, nullable=True)
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "etype_annotation_body",
    }


class DataMaturityAnnotationBody(AnnotationBody):
    __tablename__ = "datamaturity_annotation_body"
    id: Mapped[int] = mapped_column(
        ForeignKey("annotation_body.id"),
        primary_key=True,
        index=True,
        nullable=False,
        autoincrement=True,
    )
    pref_label: Mapped[str] = mapped_column(nullable=False, unique=True)
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "datamaturity_annotation_body",
    }


class Annotation(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "annotation"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    note: Mapped[str] = mapped_column(nullable=True)
    entity = relationship("Entity", back_populates="annotations")
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id"), index=True)
    annotation_body_id: Mapped[int] = mapped_column(ForeignKey("annotation_body.id"), index=True)
    annotation_body = relationship("AnnotationBody", uselist=False)


class Entity(TimestampMixin, Root):
    __tablename__ = "entity"
    id: Mapped[int] = mapped_column(ForeignKey("root.id"), primary_key=True)
    # _type: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    annotations = relationship("Annotation", back_populates="entity")
    # TODO: keep the _ ? put on agent ?
    createdBy = relationship("Agent", uselist=False, foreign_keys="Entity.createdBy_id")
    # TODO: move to mandatory
    createdBy_id: Mapped[int] = mapped_column(ForeignKey("agent.id"), index=True, nullable=True)
    updatedBy = relationship("Agent", uselist=False, foreign_keys="Entity.updatedBy_id")
    # TODO: move to mandatory
    updatedBy_id: Mapped[int] = mapped_column(ForeignKey("agent.id"), index=True, nullable=True)

    authorized_project_id: Mapped[UUID]
    authorized_public: Mapped[bool] = mapped_column(nullable=False, default=False)

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "entity",
    }


class AnalysisSoftwareSourceCode(DistributionMixin, Entity):
    __tablename__ = "analysis_software_source_code"
    id: Mapped[int] = mapped_column(
        ForeignKey("entity.id"),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    # TODO: identify what is mandatory
    branch: Mapped[str] = mapped_column(nullable=False, default="")
    codeRepository: Mapped[str] = mapped_column(nullable=False, default="")
    command: Mapped[str] = mapped_column(nullable=False, default="")
    commit: Mapped[str] = mapped_column(nullable=False, default="")
    # TODO: understand what is this
    # configurationTemplate: Mapped[str] = mapped_column(nullable=False, default="")
    description: Mapped[str] = mapped_column(nullable=False, default="")
    name: Mapped[str] = mapped_column(nullable=False, default="")
    subdirectory: Mapped[str] = mapped_column(nullable=False, default="")
    # TODO: foreign key to entity
    targetEntity: Mapped[str] = mapped_column(nullable=False, default="")
    # TODO: should be enum
    programmingLanguage: Mapped[str] = mapped_column(nullable=False, default="")
    # TODO: should be enum
    runtimePlatform: Mapped[str] = mapped_column(nullable=False, default="")
    version: Mapped[str] = mapped_column(nullable=False, default="")

    __mapper_args__ = {"polymorphic_identity": "analysis_software_source_code"}  # noqa: RUF012


class Contribution(TimestampMixin, Base):
    __tablename__ = "contribution"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agent.id"), index=True, nullable=False)
    agent = relationship("Agent", uselist=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"), index=True, nullable=False)
    role = relationship("Role", uselist=False)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id"), index=True, nullable=False)
    entity = relationship("Entity", uselist=False)
    __table_args__ = (
        UniqueConstraint("entity_id", "role_id", "agent_id", name="unique_contribution_1"),
    )


class EModel(DistributionMixin, SpeciesMixin, LocationMixin, Entity):
    __tablename__ = "emodel"
    id: Mapped[int] = mapped_column(
        ForeignKey("entity.id"),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    description: Mapped[str] = mapped_column(nullable=False, default="")
    name: Mapped[str] = mapped_column(nullable=False, default="")
    # what is this
    eModel: Mapped[str] = mapped_column(nullable=False, default="")
    # what is this
    eType: Mapped[str] = mapped_column(nullable=False, default="")
    # what is this
    iteration: Mapped[str] = mapped_column(nullable=False, default="")
    score: Mapped[float] = mapped_column(nullable=False, default=-1)
    seed: Mapped[int] = mapped_column(nullable=False, default=-1)

    __mapper_args__ = {"polymorphic_identity": "emodel"}  # noqa: RUF012


class Mesh(DistributionMixin, Entity):
    __tablename__ = "mesh"
    id: Mapped[int] = mapped_column(
        ForeignKey("entity.id"),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    brain_region_id: Mapped[int] = mapped_column(
        ForeignKey("brain_region.id"), index=True, nullable=False
    )
    brain_region = relationship("BrainRegion", uselist=False)
    __mapper_args__ = {"polymorphic_identity": "mesh"}  # noqa: RUF012


class MEModel(DistributionMixin, LocationMixin, Entity):
    __tablename__ = "memodel"
    id: Mapped[int] = mapped_column(
        ForeignKey("entity.id"),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    description: Mapped[str] = mapped_column(nullable=False, default="")
    name: Mapped[str] = mapped_column(nullable=False, default="")
    status: Mapped[str] = mapped_column(nullable=False, default="")
    validated: Mapped[bool] = mapped_column(nullable=False, default=False)
    # TODO: see how it relates to other created by properties
    __mapper_args__ = {"polymorphic_identity": "memodel"}  # noqa: RUF012


class ReconstructionMorphology(LicensedMixin, LocationMixin, SpeciesMixin, Entity):
    __tablename__ = "reconstruction_morphology"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    description: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    # name is not unique
    name: Mapped[str] = mapped_column(unique=False, index=True, nullable=False)
    morphology_description_vector: Mapped[str] = mapped_column(TSVECTOR, nullable=True)
    morphology_feature_annotation = relationship("MorphologyFeatureAnnotation", uselist=False)
    __mapper_args__ = {"polymorphic_identity": "reconstruction_morphology"}  # noqa: RUF012


class MorphologyFeatureAnnotation(TimestampMixin, Base):
    __tablename__ = "morphology_feature_annotation"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # name = mapped_column(String, unique=True, index=True, nullable=False)
    # description = mapped_column(String, unique=False, index=False, nullable=False)
    reconstruction_morphology_id: Mapped[int] = mapped_column(
        ForeignKey("reconstruction_morphology.id"), index=True, nullable=False, unique=True
    )
    reconstruction_morphology = relationship(
        "ReconstructionMorphology",
        uselist=False,
        back_populates="morphology_feature_annotation",
    )
    measurements = relationship("MorphologyMeasurement", uselist=True)


class MorphologyMeasurement(Base):
    __tablename__ = "measurement"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    measurement_of: Mapped[str] = mapped_column(unique=False, index=True, nullable=False)
    morphology_feature_annotation_id: Mapped[int] = mapped_column(
        ForeignKey("morphology_feature_annotation.id"), index=True, nullable=False
    )
    measurement_serie = relationship("MorphologyMeasurementSerieElement", uselist=True)


class MorphologyMeasurementSerieElement(Base):
    __tablename__ = "measurement_serie_element"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=False, index=False, nullable=True)
    value: Mapped[float] = mapped_column(unique=False, index=False, nullable=True)
    measurement_id: Mapped[int] = mapped_column(
        ForeignKey("measurement.id"), index=True, nullable=False
    )


class Role(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "role"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    role_id: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)


class SingleCellExperimentalTrace(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "single_cell_experimental_trace"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(unique=False, index=True, nullable=False)
    description: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "single_cell_experimental_trace"}  # noqa: RUF012


class SingleNeuronSynaptome(DistributionMixin, LocationMixin, Entity):
    __tablename__ = "single_neuron_synaptome"
    id: Mapped[int] = mapped_column(
        ForeignKey("entity.id"),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    description: Mapped[str] = mapped_column(nullable=False, default="")
    name: Mapped[str] = mapped_column(nullable=False, default="")
    seed: Mapped[int] = mapped_column(nullable=False, default=-1)
    me_model_id: Mapped[int] = mapped_column(ForeignKey("memodel.id"), index=True, nullable=False)
    me_model = relationship("MEModel", uselist=False, foreign_keys=[me_model_id])
    __mapper_args__ = {"polymorphic_identity": "single_neuron_synaptome"}  # noqa: RUF012


class SingleNeuronSimulation(DistributionMixin, LocationMixin, Entity):
    __tablename__ = "single_neuron_simulation"
    id: Mapped[int] = mapped_column(
        ForeignKey("entity.id"),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    description: Mapped[str] = mapped_column(nullable=False, default="")
    name: Mapped[str] = mapped_column(nullable=False, default="")
    seed: Mapped[int] = mapped_column(nullable=False, default=-1)
    injectionLocation: Mapped[StringList] = mapped_column(nullable=False, default="")
    recordingLocation: Mapped[StringList] = mapped_column(nullable=False, default=[])
    # TODO: called used ?
    me_model_id: Mapped[int] = mapped_column(ForeignKey("memodel.id"), index=True, nullable=False)
    me_model = relationship("MEModel", uselist=False, foreign_keys=[me_model_id])
    __mapper_args__ = {"polymorphic_identity": "single_neuron_simulation"}  # noqa: RUF012


class ExperimentalNeuronDensity(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "experimental_neuron_density"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(unique=False, index=True, nullable=False)
    description: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "experimental_neuron_density"}  # noqa: RUF012


class ExperimentalBoutonDensity(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "experimental_bouton_density"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(unique=False, index=True, nullable=False)
    description: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "experimental_bouton_density"}  # noqa: RUF012


class ExperimentalSynapsesPerConnection(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "experimental_synapses_per_connection"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(unique=False, index=True, nullable=False)
    description: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "experimental_synapses_per_connection"}  # noqa: RUF012
