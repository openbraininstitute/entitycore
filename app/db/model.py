from datetime import datetime
from typing import ClassVar
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    LargeBinary,
    MetaData,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column, relationship

from app.db.types import (
    BIGINT,
    JSONDICT,
    AssetStatus,
    PointLocation,
    PointLocationType,
    StringList,
    StringListType,
)


class Base(DeclarativeBase):
    type_annotation_map: ClassVar[dict] = {
        datetime: DateTime(timezone=True),
        StringList: StringListType,
        PointLocation: PointLocationType,
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
    legacy_id: Mapped[StringList | None] = mapped_column(index=True)


class DistributionMixin:
    content_url: Mapped[str | None]


class Root(LegacyMixin, Base):
    __tablename__ = "root"
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    type: Mapped[str]
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "root",
        "polymorphic_on": "type",
    }


class BrainRegion(TimestampMixin, Base):
    __tablename__ = "brain_region"

    # See https://github.com/openbraininstitute/core-web-app/blob/cd89893db3fe08a1d2e5ba90235ef6d8c7be6484/src/types/ontologies.ts#L7
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    acronym: Mapped[str] = mapped_column(unique=True, index=True)
    children: Mapped[list[int] | None] = mapped_column(ARRAY(BigInteger))


class Species(TimestampMixin, Base):
    __tablename__ = "species"
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    taxonomy_id: Mapped[str] = mapped_column(unique=True, index=True)


class Strain(TimestampMixin, Base):
    __tablename__ = "strain"
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    taxonomy_id: Mapped[str] = mapped_column(unique=True, index=True)
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id"), index=True)
    species = relationship("Species", uselist=False)

    __table_args__ = (
        # needed for the composite foreign key in SpeciesMixin
        UniqueConstraint("id", "species_id", name="uq_strain_id_species_id"),
    )


class Subject(TimestampMixin, Base):
    __tablename__ = "subject"
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)


class License(TimestampMixin, LegacyMixin, Base):
    __tablename__ = "license"
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    description: Mapped[str]
    label: Mapped[str]


class LicensedMixin:
    license_id: Mapped[int | None] = mapped_column(ForeignKey("license.id"), index=True)

    @declared_attr
    @classmethod
    def license(cls):
        return relationship("License", uselist=False)


class LocationMixin:
    brain_region_id: Mapped[int] = mapped_column(ForeignKey("brain_region.id"), index=True)

    @declared_attr
    @classmethod
    def brain_region(cls):
        return relationship("BrainRegion", uselist=False)


class SpeciesMixin:
    species_id: Mapped[int] = mapped_column(ForeignKey("species.id"), index=True)

    @declared_attr
    @classmethod
    def species(cls):
        return relationship("Species", uselist=False)

    # not defined as ForeignKey to avoid ambiguities with the composite foreign key
    strain_id: Mapped[int | None] = mapped_column(index=True)

    @declared_attr
    @classmethod
    def strain(cls):
        # primaryjoin is needed to ignore species_id from the ForeignKeyConstraint
        return relationship("Strain", uselist=False, primaryjoin=cls.strain_id == Strain.id)

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
    id: Mapped[int] = mapped_column(ForeignKey("root.id"), primary_key=True, autoincrement=False)
    pref_label: Mapped[str] = mapped_column(unique=True, index=True)
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "agent",
    }


class Person(Agent):
    __tablename__ = "person"

    id: Mapped[int] = mapped_column(ForeignKey("agent.id"), primary_key=True, autoincrement=False)
    givenName: Mapped[str]
    familyName: Mapped[str]

    __mapper_args__ = {"polymorphic_identity": "person"}  # noqa: RUF012
    __table_args__ = (UniqueConstraint("givenName", "familyName", name="unique_person_name_1"),)


class Organization(Agent):
    __tablename__ = "organization"

    id: Mapped[int] = mapped_column(ForeignKey("agent.id"), primary_key=True, autoincrement=False)
    # what is the difference between name and label here ?
    alternative_name: Mapped[str]

    __mapper_args__ = {"polymorphic_identity": "organization"}  # noqa: RUF012


class AnnotationBody(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "annotation_body"
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    type: Mapped[str]
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "annotation_body",
        "polymorphic_on": "type",
    }


class MTypeClass(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "mtype_class"
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    pref_label: Mapped[str] = mapped_column(unique=True, index=True)
    definition: Mapped[str]
    alt_label: Mapped[str | None]


class MTypeClassification(TimestampMixin, Base):
    __tablename__ = "mtype_classification"
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    createdBy_id: Mapped[int | None] = mapped_column(ForeignKey("agent.id"), index=True)
    updatedBy_id: Mapped[int | None] = mapped_column(ForeignKey("agent.id"), index=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id"), index=True)
    mtype_class_id: Mapped[int] = mapped_column(ForeignKey("mtype_class.id"), index=True)


class ETypeAnnotationBody(AnnotationBody):
    __tablename__ = "etype_annotation_body"
    id: Mapped[int] = mapped_column(
        ForeignKey("annotation_body.id"), primary_key=True, autoincrement=False
    )
    pref_label: Mapped[str] = mapped_column(unique=True, index=True)
    definition: Mapped[str | None]
    alt_label: Mapped[str | None]
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "etype_annotation_body",
    }


class DataMaturityAnnotationBody(AnnotationBody):
    __tablename__ = "datamaturity_annotation_body"
    id: Mapped[int] = mapped_column(
        ForeignKey("annotation_body.id"), primary_key=True, autoincrement=False
    )
    pref_label: Mapped[str] = mapped_column(unique=True, index=True)
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "datamaturity_annotation_body",
    }


class Annotation(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "annotation"
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    note: Mapped[str | None]
    entity = relationship("Entity", back_populates="annotations")
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id"), index=True)
    annotation_body_id: Mapped[int] = mapped_column(ForeignKey("annotation_body.id"), index=True)
    annotation_body = relationship("AnnotationBody", uselist=False)


class Entity(TimestampMixin, Root):
    __tablename__ = "entity"
    id: Mapped[int] = mapped_column(ForeignKey("root.id"), primary_key=True, autoincrement=False)

    # _type: Mapped[str] = mapped_column()
    annotations = relationship("Annotation", back_populates="entity")

    # TODO: keep the _ ? put on agent ?
    createdBy = relationship("Agent", uselist=False, foreign_keys="Entity.createdBy_id")
    # TODO: move to mandatory
    createdBy_id: Mapped[int | None] = mapped_column(ForeignKey("agent.id"), index=True)
    updatedBy = relationship("Agent", uselist=False, foreign_keys="Entity.updatedBy_id")
    # TODO: move to mandatory
    updatedBy_id: Mapped[int | None] = mapped_column(ForeignKey("agent.id"), index=True)

    authorized_project_id: Mapped[UUID]
    authorized_public: Mapped[bool] = mapped_column(default=False)

    contributions: Mapped[list["Contribution"]] = relationship(uselist=True, viewonly=True)

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "entity",
    }


class AnalysisSoftwareSourceCode(DistributionMixin, Entity):
    __tablename__ = "analysis_software_source_code"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True, autoincrement=False)
    # TODO: identify what is mandatory
    branch: Mapped[str] = mapped_column(default="")
    codeRepository: Mapped[str] = mapped_column(default="")
    command: Mapped[str] = mapped_column(default="")
    commit: Mapped[str] = mapped_column(default="")
    # TODO: understand what is this
    # configurationTemplate: Mapped[str] = mapped_column(default="")
    description: Mapped[str] = mapped_column(default="")
    name: Mapped[str] = mapped_column(default="")
    subdirectory: Mapped[str] = mapped_column(default="")
    # TODO: foreign key to entity
    targetEntity: Mapped[str] = mapped_column(default="")
    # TODO: should be enum
    programmingLanguage: Mapped[str] = mapped_column(default="")
    # TODO: should be enum
    runtimePlatform: Mapped[str] = mapped_column(default="")
    version: Mapped[str] = mapped_column(default="")

    __mapper_args__ = {"polymorphic_identity": "analysis_software_source_code"}  # noqa: RUF012


class Contribution(TimestampMixin, Base):
    __tablename__ = "contribution"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agent.id"), index=True)
    agent = relationship("Agent", uselist=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"), index=True)
    role = relationship("Role", uselist=False)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id"), index=True)
    entity = relationship("Entity", uselist=False)

    __table_args__ = (
        UniqueConstraint("entity_id", "role_id", "agent_id", name="unique_contribution_1"),
    )


class EModel(DistributionMixin, SpeciesMixin, LocationMixin, Entity):
    __tablename__ = "emodel"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True, autoincrement=False)
    description: Mapped[str] = mapped_column(default="")
    name: Mapped[str] = mapped_column(default="")
    # what is this
    eModel: Mapped[str] = mapped_column(default="")
    # what is this
    eType: Mapped[str] = mapped_column(default="")
    # what is this
    iteration: Mapped[str] = mapped_column(default="")
    score: Mapped[float] = mapped_column(default=-1)
    seed: Mapped[int] = mapped_column(default=-1)

    __mapper_args__ = {"polymorphic_identity": "emodel"}  # noqa: RUF012


class Mesh(DistributionMixin, LocationMixin, Entity):
    __tablename__ = "mesh"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True, autoincrement=False)
    __mapper_args__ = {"polymorphic_identity": "mesh"}  # noqa: RUF012


class MEModel(DistributionMixin, LocationMixin, Entity):
    __tablename__ = "memodel"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True, autoincrement=False)
    description: Mapped[str] = mapped_column(default="")
    name: Mapped[str] = mapped_column(default="")
    status: Mapped[str] = mapped_column(default="")
    validated: Mapped[bool] = mapped_column(default=False)
    # TODO: see how it relates to other created by properties
    __mapper_args__ = {"polymorphic_identity": "memodel"}  # noqa: RUF012


class ReconstructionMorphology(LicensedMixin, LocationMixin, SpeciesMixin, Entity):
    __tablename__ = "reconstruction_morphology"

    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True, autoincrement=False)
    description: Mapped[str]
    # name is not unique
    name: Mapped[str] = mapped_column(index=True)
    morphology_description_vector: Mapped[str | None] = mapped_column(TSVECTOR)
    morphology_feature_annotation = relationship("MorphologyFeatureAnnotation", uselist=False)

    location: Mapped[PointLocation | None]

    mtypes: Mapped[list["MTypeClass"]] = relationship(
        primaryjoin="ReconstructionMorphology.id == MTypeClassification.entity_id",
        secondary="join(mtype_classification, mtype_class)",
        uselist=True,
        viewonly=True,
    )

    __mapper_args__ = {"polymorphic_identity": "reconstruction_morphology"}  # noqa: RUF012


class MorphologyFeatureAnnotation(TimestampMixin, Base):
    __tablename__ = "morphology_feature_annotation"
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    # name = mapped_column(String, unique=True, index=True)
    # description = mapped_column(String)
    reconstruction_morphology_id: Mapped[int] = mapped_column(
        ForeignKey("reconstruction_morphology.id"), index=True, unique=True
    )
    reconstruction_morphology = relationship(
        "ReconstructionMorphology",
        uselist=False,
        back_populates="morphology_feature_annotation",
    )
    measurements = relationship("MorphologyMeasurement", uselist=True)


class MorphologyMeasurement(Base):
    __tablename__ = "measurement"
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    measurement_of: Mapped[str] = mapped_column(index=True)
    morphology_feature_annotation_id: Mapped[int] = mapped_column(
        ForeignKey("morphology_feature_annotation.id"), index=True
    )
    measurement_serie = relationship("MorphologyMeasurementSerieElement", uselist=True)


class MorphologyMeasurementSerieElement(Base):
    __tablename__ = "measurement_serie_element"
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str | None]
    value: Mapped[float | None]
    measurement_id: Mapped[int] = mapped_column(ForeignKey("measurement.id"), index=True)


class Role(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "role"
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    role_id: Mapped[str] = mapped_column(unique=True, index=True)


class SingleCellExperimentalTrace(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "single_cell_experimental_trace"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str]
    __mapper_args__ = {"polymorphic_identity": "single_cell_experimental_trace"}  # noqa: RUF012


class SingleNeuronSynaptome(DistributionMixin, LocationMixin, Entity):
    __tablename__ = "single_neuron_synaptome"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True, autoincrement=False)
    description: Mapped[str] = mapped_column(default="")
    name: Mapped[str] = mapped_column(default="")
    seed: Mapped[int] = mapped_column(default=-1)
    me_model_id: Mapped[int] = mapped_column(ForeignKey("memodel.id"), index=True)
    me_model = relationship("MEModel", uselist=False, foreign_keys=[me_model_id])
    __mapper_args__ = {"polymorphic_identity": "single_neuron_synaptome"}  # noqa: RUF012


class SingleNeuronSimulation(DistributionMixin, LocationMixin, Entity):
    __tablename__ = "single_neuron_simulation"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True, autoincrement=False)
    description: Mapped[str] = mapped_column(default="")
    name: Mapped[str] = mapped_column(default="")
    seed: Mapped[int] = mapped_column(default=-1)
    injectionLocation: Mapped[StringList] = mapped_column(default="")
    recordingLocation: Mapped[StringList] = mapped_column(default=[])
    # TODO: called used ?
    me_model_id: Mapped[int] = mapped_column(ForeignKey("memodel.id"), index=True)
    me_model = relationship("MEModel", uselist=False, foreign_keys=[me_model_id])
    __mapper_args__ = {"polymorphic_identity": "single_neuron_simulation"}  # noqa: RUF012


class ExperimentalNeuronDensity(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "experimental_neuron_density"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str]
    __mapper_args__ = {"polymorphic_identity": "experimental_neuron_density"}  # noqa: RUF012


class ExperimentalBoutonDensity(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "experimental_bouton_density"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str]
    __mapper_args__ = {"polymorphic_identity": "experimental_bouton_density"}  # noqa: RUF012


class ExperimentalSynapsesPerConnection(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "experimental_synapses_per_connection"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str]
    __mapper_args__ = {"polymorphic_identity": "experimental_synapses_per_connection"}  # noqa: RUF012


class Asset(TimestampMixin, Base):
    """Asset table."""

    __tablename__ = "asset"
    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    status: Mapped[AssetStatus] = mapped_column()
    path: Mapped[str]  # relative path
    full_path: Mapped[str]  # full path on S3
    bucket_name: Mapped[str]
    is_directory: Mapped[bool]
    content_type: Mapped[str]
    size: Mapped[BIGINT]
    sha256_digest: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    meta: Mapped[JSONDICT]  # not used yet. can be useful?
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id"), index=True)

    # partial unique index
    __table_args__ = (
        Index(
            "ix_asset_full_path",
            "full_path",
            unique=True,
            postgresql_where=(status != AssetStatus.DELETED.name),
        ),
    )
