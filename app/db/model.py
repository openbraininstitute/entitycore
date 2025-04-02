import enum
import uuid
from datetime import datetime
from typing import ClassVar

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
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
    JSON_DICT,
    STRING_LIST,
    AssetStatus,
    PointLocation,
    PointLocationType,
    SingleNeuronSimulationStatus,
)
from app.utils.uuid import create_uuid


class Base(DeclarativeBase):
    type_annotation_map: ClassVar[dict] = {
        datetime: DateTime(timezone=True),
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
    legacy_id: Mapped[STRING_LIST | None] = mapped_column(index=True)
    legacy_self: Mapped[STRING_LIST | None]


class Identifiable(Base):
    __abstract__ = True  # This class is abstract and not directly mapped to a table
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=create_uuid)


class Root(LegacyMixin, Identifiable):
    __tablename__ = "root"
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


class Species(TimestampMixin, Identifiable):
    __tablename__ = "species"
    name: Mapped[str] = mapped_column(unique=True, index=True)
    taxonomy_id: Mapped[str] = mapped_column(unique=True, index=True)


class Strain(TimestampMixin, Identifiable):
    __tablename__ = "strain"
    name: Mapped[str] = mapped_column(unique=True, index=True)
    taxonomy_id: Mapped[str] = mapped_column(unique=True, index=True)
    species_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("species.id"), index=True)
    species = relationship("Species", uselist=False)

    __table_args__ = (
        # needed for the composite foreign key in SpeciesMixin
        UniqueConstraint("id", "species_id", name="uq_strain_id_species_id"),
    )


class Subject(TimestampMixin, Identifiable):
    __tablename__ = "subject"
    name: Mapped[str] = mapped_column(unique=True, index=True)


class License(TimestampMixin, LegacyMixin, Identifiable):
    __tablename__ = "license"
    name: Mapped[str] = mapped_column(unique=True, index=True)
    description: Mapped[str]
    label: Mapped[str]


class LicensedMixin:
    license_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("license.id"), index=True)

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
    species_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("species.id"), index=True)

    @declared_attr
    @classmethod
    def species(cls):
        return relationship("Species", uselist=False)

    # not defined as ForeignKey to avoid ambiguities with the composite foreign key
    strain_id: Mapped[uuid.UUID | None] = mapped_column(index=True)

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
            *getattr(super(), "__table_args__", ()),
        )


class Agent(TimestampMixin, Root):
    __tablename__ = "agent"
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("root.id"), primary_key=True)
    pref_label: Mapped[str] = mapped_column(unique=True, index=True)
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "agent",
    }


class Person(Agent):
    __tablename__ = "person"

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent.id"), primary_key=True)
    givenName: Mapped[str]
    familyName: Mapped[str]

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "person",
        "polymorphic_load": "selectin",
    }
    __table_args__ = (UniqueConstraint("givenName", "familyName", name="unique_person_name_1"),)


class Organization(Agent):
    __tablename__ = "organization"

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent.id"), primary_key=True)
    # what is the difference between name and label here ?
    alternative_name: Mapped[str]

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "organization",
        "polymorphic_load": "selectin",
    }


class AnnotationBody(LegacyMixin, TimestampMixin, Identifiable):
    __tablename__ = "annotation_body"
    type: Mapped[str]
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "annotation_body",
        "polymorphic_on": "type",
    }


class AnnotationMixin:
    pref_label: Mapped[str] = mapped_column(unique=True, index=True)
    definition: Mapped[str]
    alt_label: Mapped[str | None]


class ClassificationMixin:
    createdBy_id: Mapped[int | None] = mapped_column(ForeignKey("agent.id"), index=True)
    updatedBy_id: Mapped[int | None] = mapped_column(ForeignKey("agent.id"), index=True)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id"), index=True)


class MTypeClass(AnnotationMixin, LegacyMixin, TimestampMixin, Identifiable):
    __tablename__ = "mtype_class"


class ETypeClass(AnnotationMixin, LegacyMixin, TimestampMixin, Identifiable):
    __tablename__ = "etype_class"


class MTypeClassification(ClassificationMixin, TimestampMixin, Identifiable):
    __tablename__ = "mtype_classification"

    mtype_class_id: Mapped[int] = mapped_column(ForeignKey("mtype_class.id"), index=True)


class ETypeClassification(ClassificationMixin, TimestampMixin, Identifiable):
    __tablename__ = "etype_classification"

    etype_class_id: Mapped[int] = mapped_column(ForeignKey("etype_class.id"), index=True)


class MTypesMixin:
    @declared_attr
    @classmethod
    def mtypes(cls) -> Mapped[list["MTypeClass"]]:
        if not issubclass(cls, Entity):
            msg = f"{cls} should be an Entity"
            raise TypeError(msg)

        return relationship(
            primaryjoin=f"{cls.__name__}.id == MTypeClassification.entity_id",
            secondary="mtype_classification",
            uselist=True,
            viewonly=True,
            order_by="MTypeClass.pref_label",
        )


class ETypesMixin:
    @declared_attr
    @classmethod
    def etypes(cls) -> Mapped[list["ETypeClass"]]:
        if not issubclass(cls, Entity):
            msg = f"{cls} should be an Entity"
            raise TypeError(msg)

        return relationship(
            primaryjoin=f"{cls.__name__}.id == ETypeClassification.entity_id",
            secondary="etype_classification",
            uselist=True,
            viewonly=True,
            order_by="ETypeClass.pref_label",
        )


class DataMaturityAnnotationBody(AnnotationBody):
    __tablename__ = "datamaturity_annotation_body"
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("annotation_body.id"), primary_key=True)
    pref_label: Mapped[str] = mapped_column(unique=True, index=True)
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "datamaturity_annotation_body",
    }


class Annotation(LegacyMixin, TimestampMixin, Identifiable):
    __tablename__ = "annotation"
    note: Mapped[str | None]
    entity = relationship("Entity", back_populates="annotations")
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), index=True)
    annotation_body_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("annotation_body.id"), index=True
    )
    annotation_body = relationship("AnnotationBody", uselist=False)


class DescriptionVectorMixin:
    description_vector: Mapped[str | None] = mapped_column(TSVECTOR)

    @declared_attr.directive
    @classmethod
    def __table_args__(cls):  # noqa: D105, PLW3201
        return (
            Index(
                f"ix_{cls.__tablename__}_description_vector",
                cls.description_vector,
                postgresql_using="gin",
            ),
            *getattr(super(), "__table_args__", ()),
        )


class Entity(TimestampMixin, Root):
    __tablename__ = "entity"
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("root.id"), primary_key=True)

    # _type: Mapped[str] = mapped_column()
    annotations = relationship("Annotation", back_populates="entity")

    # TODO: keep the _ ? put on agent ?
    createdBy = relationship("Agent", uselist=False, foreign_keys="Entity.createdBy_id")
    # TODO: move to mandatory
    createdBy_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agent.id"), index=True)
    updatedBy = relationship("Agent", uselist=False, foreign_keys="Entity.updatedBy_id")
    # TODO: move to mandatory
    updatedBy_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agent.id"), index=True)

    authorized_project_id: Mapped[uuid.UUID]
    authorized_public: Mapped[bool] = mapped_column(default=False)

    contributions: Mapped[list["Contribution"]] = relationship(uselist=True, viewonly=True)
    assets: Mapped[list["Asset"]] = relationship(
        "Asset",
        foreign_keys="Asset.entity_id",
        uselist=True,
        viewonly=True,
    )

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": "entity",
    }


class AnalysisSoftwareSourceCode(Entity):
    __tablename__ = "analysis_software_source_code"
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
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


class Contribution(TimestampMixin, Identifiable):
    __tablename__ = "contribution"
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent.id"), index=True)
    agent = relationship("Agent", uselist=False)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("role.id"), index=True)
    role = relationship("Role", uselist=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), index=True)
    entity = relationship("Entity", uselist=False)

    __table_args__ = (
        UniqueConstraint("entity_id", "role_id", "agent_id", name="unique_contribution_1"),
    )


class EModel(MTypesMixin, ETypesMixin, DescriptionVectorMixin, SpeciesMixin, LocationMixin, Entity):
    __tablename__ = "emodel"
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
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

    exemplar_morphology_id: Mapped[int] = mapped_column(
        ForeignKey("reconstruction_morphology.id"), nullable=False
    )

    exemplar_morphology = relationship(
        "ReconstructionMorphology", foreign_keys=[exemplar_morphology_id], uselist=False
    )

    __mapper_args__ = {"polymorphic_identity": "emodel"}  # noqa: RUF012


class Mesh(LocationMixin, Entity):
    __tablename__ = "mesh"
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": "mesh"}  # noqa: RUF012


class ValidationStatus(enum.Enum):
    created = "created"
    initialized = "initialized"
    running = "running"
    done = "done"
    error = "error"


class MEModel(
    MTypesMixin, ETypesMixin, DescriptionVectorMixin, SpeciesMixin, LocationMixin, Entity
):
    __tablename__ = "memodel"
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    description: Mapped[str] = mapped_column(default="")
    name: Mapped[str] = mapped_column(default="")

    validation_status: Mapped[ValidationStatus] = mapped_column(
        Enum(ValidationStatus, name="me_model_validation_status"),
        nullable=False,
        default=ValidationStatus.created,
    )

    morphology_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reconstruction_morphology.id"), nullable=False
    )

    morphology = relationship(
        "ReconstructionMorphology", foreign_keys=[morphology_id], uselist=False
    )

    emodel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("emodel.id"), nullable=False)

    emodel = relationship("EModel", foreign_keys=[emodel_id], uselist=False)

    __mapper_args__ = {"polymorphic_identity": "memodel"}  # noqa: RUF012


class ReconstructionMorphology(
    MTypesMixin, DescriptionVectorMixin, LicensedMixin, LocationMixin, SpeciesMixin, Entity
):
    __tablename__ = "reconstruction_morphology"

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    description: Mapped[str]
    # name is not unique
    name: Mapped[str] = mapped_column(index=True)
    morphology_feature_annotation = relationship("MorphologyFeatureAnnotation", uselist=False)

    location: Mapped[PointLocation | None]

    __mapper_args__ = {"polymorphic_identity": "reconstruction_morphology"}  # noqa: RUF012


class MorphologyFeatureAnnotation(TimestampMixin, Identifiable):
    __tablename__ = "morphology_feature_annotation"
    # name = mapped_column(String, unique=True, index=True)
    # description = mapped_column(String)
    reconstruction_morphology_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reconstruction_morphology.id"), index=True, unique=True
    )
    reconstruction_morphology = relationship(
        "ReconstructionMorphology",
        uselist=False,
        back_populates="morphology_feature_annotation",
    )
    measurements = relationship("MorphologyMeasurement", uselist=True)


class MorphologyMeasurement(Identifiable):
    __tablename__ = "measurement"
    measurement_of: Mapped[str] = mapped_column(index=True)
    morphology_feature_annotation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("morphology_feature_annotation.id"), index=True
    )
    measurement_serie = relationship("MorphologyMeasurementSerieElement", uselist=True)


class MorphologyMeasurementSerieElement(Identifiable):
    __tablename__ = "measurement_serie_element"
    name: Mapped[str | None]
    value: Mapped[float | None]
    measurement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("measurement.id"), index=True)


class Role(LegacyMixin, TimestampMixin, Identifiable):
    __tablename__ = "role"
    name: Mapped[str] = mapped_column(unique=True, index=True)
    role_id: Mapped[str] = mapped_column(unique=True, index=True)


class SingleCellExperimentalTrace(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "single_cell_experimental_trace"
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str]
    __mapper_args__ = {"polymorphic_identity": "single_cell_experimental_trace"}  # noqa: RUF012


class SingleNeuronSynaptome(DescriptionVectorMixin, LocationMixin, Entity):
    __tablename__ = "single_neuron_synaptome"
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    description: Mapped[str] = mapped_column(default="")
    name: Mapped[str]
    seed: Mapped[int]
    me_model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("memodel.id"), index=True)
    me_model = relationship("MEModel", uselist=False, foreign_keys=[me_model_id])
    __mapper_args__ = {"polymorphic_identity": "single_neuron_synaptome"}  # noqa: RUF012


class SingleNeuronSimulation(DescriptionVectorMixin, LocationMixin, Entity):
    __tablename__ = "single_neuron_simulation"
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    description: Mapped[str] = mapped_column(default="")
    name: Mapped[str]
    seed: Mapped[int]
    injectionLocation: Mapped[STRING_LIST] = mapped_column(default=[])
    recordingLocation: Mapped[STRING_LIST] = mapped_column(default=[])
    status: Mapped[SingleNeuronSimulationStatus]
    # TODO: called used ?
    me_model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("memodel.id"), index=True)
    me_model = relationship("MEModel", uselist=False, foreign_keys=[me_model_id])
    __mapper_args__ = {"polymorphic_identity": "single_neuron_simulation"}  # noqa: RUF012


class SingleNeuronSynaptomeSimulation(DescriptionVectorMixin, LocationMixin, Entity):
    __tablename__ = "single_neuron_synaptome_simulation"
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    description: Mapped[str] = mapped_column(default="")
    name: Mapped[str]
    seed: Mapped[int]
    injectionLocation: Mapped[STRING_LIST] = mapped_column(default=[])
    recordingLocation: Mapped[STRING_LIST] = mapped_column(default=[])
    status: Mapped[SingleNeuronSimulationStatus]
    synaptome_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("single_neuron_synaptome.id"), index=True
    )
    synaptome = relationship("SingleNeuronSynaptome", uselist=False, foreign_keys=[synaptome_id])
    __mapper_args__ = {"polymorphic_identity": "single_neuron_synaptome_simulation"}  # noqa: RUF012


class ExperimentalNeuronDensity(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "experimental_neuron_density"
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str]
    __mapper_args__ = {"polymorphic_identity": "experimental_neuron_density"}  # noqa: RUF012


class ExperimentalBoutonDensity(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "experimental_bouton_density"
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str]
    __mapper_args__ = {"polymorphic_identity": "experimental_bouton_density"}  # noqa: RUF012


class ExperimentalSynapsesPerConnection(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "experimental_synapses_per_connection"
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str]
    __mapper_args__ = {"polymorphic_identity": "experimental_synapses_per_connection"}  # noqa: RUF012


class Asset(TimestampMixin, Identifiable):
    """Asset table."""

    __tablename__ = "asset"
    status: Mapped[AssetStatus] = mapped_column()
    path: Mapped[str]  # relative path
    full_path: Mapped[str]  # full path on S3
    bucket_name: Mapped[str]
    is_directory: Mapped[bool]
    content_type: Mapped[str]
    size: Mapped[BIGINT]
    sha256_digest: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    meta: Mapped[JSON_DICT]  # not used yet. can be useful?
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), index=True)

    # partial unique index
    __table_args__ = (
        Index(
            "ix_asset_full_path",
            "full_path",
            unique=True,
            postgresql_where=(status != AssetStatus.DELETED.name),
        ),
    )
