import uuid
from datetime import datetime
from typing import ClassVar

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
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
    JSON_DICT,
    STRING_LIST,
    AgentType,
    AnnotationBodyType,
    AssetStatus,
    EntityType,
    PointLocation,
    PointLocationType,
    SingleNeuronSimulationStatus,
    ValidationStatus,
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


class Identifiable(TimestampMixin, Base):
    __abstract__ = True  # This class is abstract and not directly mapped to a table
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=create_uuid)


class BrainRegion(TimestampMixin, Base):
    __tablename__ = "brain_region"

    # See https://github.com/openbraininstitute/core-web-app/blob/cd89893db3fe08a1d2e5ba90235ef6d8c7be6484/src/types/ontologies.ts#L7
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    acronym: Mapped[str] = mapped_column(unique=True, index=True)
    children: Mapped[list[int] | None] = mapped_column(ARRAY(BigInteger))


class Species(Identifiable):
    __tablename__ = "species"
    name: Mapped[str] = mapped_column(unique=True, index=True)
    taxonomy_id: Mapped[str] = mapped_column(unique=True, index=True)


class Strain(Identifiable):
    __tablename__ = "strain"
    name: Mapped[str] = mapped_column(unique=True, index=True)
    taxonomy_id: Mapped[str] = mapped_column(unique=True, index=True)
    species_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("species.id"), index=True)
    species = relationship("Species", uselist=False)

    __table_args__ = (
        # needed for the composite foreign key in SpeciesMixin
        UniqueConstraint("id", "species_id", name="uq_strain_id_species_id"),
    )


class Subject(Identifiable):
    __tablename__ = "subject"
    name: Mapped[str] = mapped_column(unique=True, index=True)


class License(LegacyMixin, Identifiable):
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


class SpeciesMixin(Base):
    __abstract__ = True
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


class Agent(LegacyMixin, Identifiable):
    __tablename__ = "agent"
    type: Mapped[AgentType]
    pref_label: Mapped[str] = mapped_column(unique=True, index=True)
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
        "polymorphic_on": "type",
    }


class Person(Agent):
    __tablename__ = AgentType.person.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent.id"), primary_key=True)
    givenName: Mapped[str]
    familyName: Mapped[str]

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
        "polymorphic_load": "selectin",
    }
    __table_args__ = (UniqueConstraint("givenName", "familyName", name="unique_person_name_1"),)


class Organization(Agent):
    __tablename__ = AgentType.organization.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent.id"), primary_key=True)
    # what is the difference between name and label here ?
    alternative_name: Mapped[str]

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
        "polymorphic_load": "selectin",
    }


class AnnotationBody(LegacyMixin, Identifiable):
    __tablename__ = "annotation_body"
    type: Mapped[AnnotationBodyType]
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
        "polymorphic_on": "type",
    }


class AnnotationMixin:
    pref_label: Mapped[str] = mapped_column(unique=True, index=True)
    definition: Mapped[str]
    alt_label: Mapped[str | None]


class ClassificationMixin:
    createdBy_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agent.id"), index=True)
    updatedBy_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agent.id"), index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), index=True)


class MTypeClass(AnnotationMixin, LegacyMixin, Identifiable):
    __tablename__ = "mtype_class"


class ETypeClass(AnnotationMixin, LegacyMixin, Identifiable):
    __tablename__ = "etype_class"


class MTypeClassification(ClassificationMixin, Identifiable):
    __tablename__ = "mtype_classification"

    mtype_class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mtype_class.id"), index=True)


class ETypeClassification(ClassificationMixin, Identifiable):
    __tablename__ = "etype_classification"

    etype_class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("etype_class.id"), index=True)


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
    __tablename__ = AnnotationBodyType.datamaturity_annotation_body.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("annotation_body.id"), primary_key=True)
    pref_label: Mapped[str] = mapped_column(unique=True, index=True)
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
    }


class Annotation(LegacyMixin, Identifiable):
    __tablename__ = "annotation"
    note: Mapped[str | None]
    entity = relationship("Entity", back_populates="annotations")
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), index=True)
    annotation_body_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("annotation_body.id"), index=True
    )
    annotation_body = relationship("AnnotationBody", uselist=False)


class DescriptionVectorMixin(Base):
    __abstract__ = True
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


class Entity(LegacyMixin, Identifiable):
    __tablename__ = "entity"

    type: Mapped[EntityType]
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
        "polymorphic_identity": __tablename__,
        "polymorphic_on": "type",
    }


class AnalysisSoftwareSourceCode(Entity):
    __tablename__ = EntityType.analysis_software_source_code.value
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

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class Contribution(Identifiable):
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
    __tablename__ = EntityType.emodel.value
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

    exemplar_morphology_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{EntityType.reconstruction_morphology}.id")
    )

    exemplar_morphology = relationship(
        "ReconstructionMorphology", foreign_keys=[exemplar_morphology_id], uselist=False
    )

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class Mesh(LocationMixin, Entity):
    __tablename__ = EntityType.mesh.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class MEModel(
    MTypesMixin, ETypesMixin, DescriptionVectorMixin, SpeciesMixin, LocationMixin, Entity
):
    __tablename__ = EntityType.memodel.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    description: Mapped[str] = mapped_column(default="")
    name: Mapped[str] = mapped_column(default="")

    validation_status: Mapped[ValidationStatus] = mapped_column(
        Enum(ValidationStatus, name="me_model_validation_status"),
        default=ValidationStatus.created,
    )

    morphology_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{EntityType.reconstruction_morphology}.id")
    )

    morphology = relationship(
        "ReconstructionMorphology", foreign_keys=[morphology_id], uselist=False
    )

    emodel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{EntityType.emodel}.id"))

    emodel = relationship("EModel", foreign_keys=[emodel_id], uselist=False)

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class ReconstructionMorphology(
    MTypesMixin, DescriptionVectorMixin, LicensedMixin, LocationMixin, SpeciesMixin, Entity
):
    __tablename__ = EntityType.reconstruction_morphology.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    description: Mapped[str]
    # name is not unique
    name: Mapped[str] = mapped_column(index=True)
    morphology_feature_annotation = relationship("MorphologyFeatureAnnotation", uselist=False)

    location: Mapped[PointLocation | None]

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class MorphologyFeatureAnnotation(Identifiable):
    __tablename__ = "morphology_feature_annotation"
    # name = mapped_column(String, unique=True, index=True)
    # description = mapped_column(String)
    reconstruction_morphology_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{EntityType.reconstruction_morphology}.id"), index=True, unique=True
    )
    reconstruction_morphology = relationship(
        "ReconstructionMorphology",
        uselist=False,
        back_populates="morphology_feature_annotation",
    )
    measurements = relationship("MorphologyMeasurement", uselist=True)


class MorphologyMeasurement(Base):
    __tablename__ = "measurement"
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    measurement_of: Mapped[str] = mapped_column(index=True)
    morphology_feature_annotation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("morphology_feature_annotation.id"), index=True
    )
    measurement_serie = relationship("MorphologyMeasurementSerieElement", uselist=True)


class MorphologyMeasurementSerieElement(Base):
    __tablename__ = "measurement_serie_element"
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str | None]
    value: Mapped[float | None]
    measurement_id: Mapped[int] = mapped_column(ForeignKey("measurement.id"), index=True)


class Role(LegacyMixin, Identifiable):
    __tablename__ = "role"
    name: Mapped[str] = mapped_column(unique=True, index=True)
    role_id: Mapped[str] = mapped_column(unique=True, index=True)


class SingleCellExperimentalTrace(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = EntityType.single_cell_experimental_trace.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str]
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class SingleNeuronSynaptome(DescriptionVectorMixin, LocationMixin, Entity):
    __tablename__ = EntityType.single_neuron_synaptome.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    description: Mapped[str] = mapped_column(default="")
    name: Mapped[str]
    seed: Mapped[int]
    me_model_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{EntityType.memodel}.id"), index=True
    )
    me_model = relationship("MEModel", uselist=False, foreign_keys=[me_model_id])
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class SingleNeuronSimulation(DescriptionVectorMixin, LocationMixin, Entity):
    __tablename__ = EntityType.single_neuron_simulation.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    description: Mapped[str] = mapped_column(default="")
    name: Mapped[str]
    seed: Mapped[int]
    injectionLocation: Mapped[STRING_LIST] = mapped_column(default=[])
    recordingLocation: Mapped[STRING_LIST] = mapped_column(default=[])
    status: Mapped[SingleNeuronSimulationStatus]
    # TODO: called used ?
    me_model_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{EntityType.memodel}.id"), index=True
    )
    me_model = relationship("MEModel", uselist=False, foreign_keys=[me_model_id])
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class SingleNeuronSynaptomeSimulation(DescriptionVectorMixin, LocationMixin, Entity):
    __tablename__ = EntityType.single_neuron_synaptome_simulation.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    description: Mapped[str] = mapped_column(default="")
    name: Mapped[str]
    seed: Mapped[int]
    injectionLocation: Mapped[STRING_LIST] = mapped_column(default=[])
    recordingLocation: Mapped[STRING_LIST] = mapped_column(default=[])
    status: Mapped[SingleNeuronSimulationStatus]
    synaptome_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{EntityType.single_neuron_synaptome}.id"), index=True
    )
    synaptome = relationship("SingleNeuronSynaptome", uselist=False, foreign_keys=[synaptome_id])
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class ExperimentalNeuronDensity(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = EntityType.experimental_neuron_density.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str]
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class ExperimentalBoutonDensity(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = EntityType.experimental_bouton_density.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str]
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class ExperimentalSynapsesPerConnection(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = EntityType.experimental_synapses_per_connection.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str]
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class Ion(Identifiable):
    __tablename__ = "ion"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=create_uuid)
    name: Mapped[str] = mapped_column(unique=True, index=True)


class IonToIonChannelModel(Base):
    __tablename__ = "ion__ion_channel_model"

    ion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ion.id", ondelete="CASCADE"), primary_key=True
    )
    ion_channel_model_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{EntityType.ion_channel_model}.id", ondelete="CASCADE"), primary_key=True
    )


class IonChannelModel(DescriptionVectorMixin, LocationMixin, SpeciesMixin, Entity):
    __tablename__ = EntityType.ion_channel_model.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)

    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str] = mapped_column(default="")
    identifier: Mapped[str]
    modelId: Mapped[str]
    is_ljp_corrected: Mapped[bool] = mapped_column(default=False)
    is_temperature_dependent: Mapped[bool] = mapped_column(default=False)
    temperature_celsius: Mapped[int]

    nmodl_parameters: Mapped[JSON_DICT]

    emodel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{EntityType.emodel}.id"))

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class IonChannelModelToEModel(Base):
    __tablename__ = "ion_channel_model__emodel"

    ion_channel_model_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{EntityType.ion_channel_model}.id", ondelete="CASCADE"), primary_key=True
    )
    emodel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{EntityType.emodel}.id", ondelete="CASCADE"), primary_key=True
    )


class Asset(Identifiable):
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
