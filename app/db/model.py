# Standard library imports
import uuid
from datetime import datetime, timedelta
from typing import ClassVar
from uuid import UUID

# Third-party imports
import sqlalchemy as sa
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
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
    relationship,
    validates,
)

# Local application imports
from app.db.types import (
    BIGINT,
    JSON_DICT,
    STRING_LIST,
    AgentType,
    AgePeriod,
    AnnotationBodyType,
    AssetLabel,
    AssetStatus,
    ElectricalRecordingOrigin,
    ElectricalRecordingStimulusShape,
    ElectricalRecordingStimulusType,
    ElectricalRecordingType,
    EntityType,
    MeasurementStatistic,
    MeasurementUnit,
    PointLocation,
    PointLocationType,
    Sex,
    SingleNeuronSimulationStatus,
    StructuralDomain,
    ValidationStatus,
)
from app.schemas.scientific_artifact import Author, PublicationType
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


class BrainRegionHierarchy(Identifiable):
    __tablename__ = "brain_region_hierarchy"

    name: Mapped[str] = mapped_column(unique=True, index=True)


class BrainRegion(Identifiable):
    __tablename__ = "brain_region"

    annotation_value: Mapped[int] = mapped_column(BigInteger, index=True)
    name: Mapped[str] = mapped_column(index=True)
    acronym: Mapped[str] = mapped_column(index=True)
    color_hex_triplet: Mapped[str] = mapped_column(String(6))
    parent_structure_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brain_region.id"), index=True, nullable=True
    )

    hierarchy_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brain_region_hierarchy.id"), index=True
    )


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
    brain_region_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brain_region.id"), index=True)

    @declared_attr
    @classmethod
    def brain_region(cls):
        return relationship("BrainRegion", uselist=False, foreign_keys=[cls.brain_region_id])


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
    given_name: Mapped[str | None]
    family_name: Mapped[str | None]
    sub_id: Mapped[uuid.UUID | None] = mapped_column(unique=True, index=True)

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
        "polymorphic_load": "selectin",
    }
    __table_args__ = (UniqueConstraint("given_name", "family_name", name="unique_person_name_1"),)


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
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agent.id"), index=True)
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agent.id"), index=True)
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


class NameDescriptionVectorMixin(Base):
    __abstract__ = True
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str] = mapped_column(default="")
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
    created_by = relationship("Agent", uselist=False, foreign_keys="Entity.created_by_id")
    # TODO: move to mandatory
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agent.id"), index=True)
    updated_by = relationship("Agent", uselist=False, foreign_keys="Entity.updated_by_id")
    # TODO: move to mandatory
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("agent.id"), index=True)

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


class Publication(Entity, NameDescriptionVectorMixin):
    """Database model for PublicationBase."""

    __tablename__ = EntityType.publication.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    DOI: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    PMID: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    original_source_location: Mapped[str | None] = mapped_column(String, nullable=True)
    other: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    authors: Mapped[list[Author] | None] = mapped_column(JSONB, nullable=True)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    journal: Mapped[str | None] = mapped_column(String, nullable=True)
    publication_year: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    abstract: Mapped[str | None] = mapped_column(String, nullable=True)

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
    }


class PublishedIn(Identifiable):

    """Database model for PublishedInBase."""

    __tablename__ = "published_in"
    publication_id: Mapped[UUID] = mapped_column(
        ForeignKey("publication.id"), primary_key=True, index=True
    )
    publication_type: Mapped[PublicationType] = mapped_column(
        Enum(PublicationType, name="publicationtype_publishedin"), primary_key=True
    )
    scientific_artifact_id: Mapped[UUID] = mapped_column(
        ForeignKey("scientific_artifact.id"), primary_key=True, index=True
    )

    # Relationships - assuming ScientificArtifact and Publication exist
    publication: Mapped["Publication"] = relationship(
        "Publication",
        foreign_keys=[publication_id],
        uselist=False,
    )
    scientific_artifact: Mapped["ScientificArtifact"] = relationship(
        "ScientificArtifact",
        foreign_keys=[scientific_artifact_id],
        uselist=False,
    )

    __table_args__ = (
        UniqueConstraint("publication_id", "scientific_artifact_id", name="uq_publishedin_ids"),
        {"extend_existing": True},
    )


class SubjectMixin:
    subject_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("subject.id"), index=True)

    @declared_attr
    @classmethod
    def subject(cls):
        return relationship("Subject", uselist=False, foreign_keys=cls.subject_id)


class ScientificArtifact(
    Entity, SubjectMixin, NameDescriptionVectorMixin, LocationMixin, LicensedMixin
):
    """Base class for scientific artifacts."""

    __tablename__ = __tablename__ = EntityType.scientific_artifact.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    experiment_date: Mapped[datetime | None] = mapped_column(DateTime)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("person.id"), nullable=True)

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
    }


class Subject(NameDescriptionVectorMixin, SpeciesMixin, Entity):
    __tablename__ = EntityType.subject.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    age_value: Mapped[timedelta | None]
    age_min: Mapped[timedelta | None]
    age_max: Mapped[timedelta | None]
    age_period: Mapped[AgePeriod | None]
    sex: Mapped[Sex | None]
    weight: Mapped[float | None]  # in grams

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class AnalysisSoftwareSourceCode(NameDescriptionVectorMixin, Entity):
    __tablename__ = EntityType.analysis_software_source_code.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    # TODO: identify what is mandatory
    branch: Mapped[str] = mapped_column(default="")
    codeRepository: Mapped[str] = mapped_column(default="")
    command: Mapped[str] = mapped_column(default="")
    commit: Mapped[str] = mapped_column(default="")
    # TODO: understand what is this
    # configurationTemplate: Mapped[str] = mapped_column(default="")
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


class EModel(
    MTypesMixin, ETypesMixin, SpeciesMixin, LocationMixin, NameDescriptionVectorMixin, Entity
):
    __tablename__ = EntityType.emodel.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
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

    ion_channel_models: Mapped[list["IonChannelModel"]] = relationship(
        primaryjoin="EModel.id == IonChannelModelToEModel.emodel_id",
        secondary="ion_channel_model__emodel",
        uselist=True,
        viewonly=True,
        order_by="IonChannelModel.creation_date",
    )

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class Mesh(LocationMixin, NameDescriptionVectorMixin, Entity):
    __tablename__ = EntityType.mesh.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class MEModel(
    MTypesMixin, ETypesMixin, SpeciesMixin, LocationMixin, NameDescriptionVectorMixin, Entity
):
    __tablename__ = EntityType.memodel.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)

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

    holding_current: Mapped[float | None]
    threshold_current: Mapped[float | None]

    emodel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{EntityType.emodel}.id"))

    emodel = relationship("EModel", foreign_keys=[emodel_id], uselist=False)

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class MeasurableEntity(Entity):
    """Abstract class for measurable entities."""

    __abstract__ = True

    @declared_attr
    @classmethod
    def measurement_annotation(cls):
        return relationship(
            "MeasurementAnnotation",
            foreign_keys="MeasurementAnnotation.entity_id",
            uselist=False,
            viewonly=True,
        )


class ReconstructionMorphology(
    MTypesMixin,
    LicensedMixin,
    LocationMixin,
    SpeciesMixin,
    NameDescriptionVectorMixin,
    MeasurableEntity,
):
    __tablename__ = EntityType.reconstruction_morphology.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    location: Mapped[PointLocation | None]

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class MeasurementAnnotation(LegacyMixin, Identifiable):
    __tablename__ = "measurement_annotation"
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), index=True, unique=True)
    entity: Mapped["Entity"] = relationship(
        viewonly=True,
        foreign_keys=[entity_id],
        primaryjoin=entity_id == Entity.id,
        lazy="raise",
    )
    measurement_kinds: Mapped[list["MeasurementKind"]] = relationship(
        back_populates="measurement_annotation", passive_deletes=True
    )

    @hybrid_property
    def entity_type(self) -> str:
        """Return the type of the associated Entity as a string.

        This is a hybrid property that can be used in Python expressions.
        """
        return str(self.entity.type)

    @entity_type.inplace.expression
    @classmethod
    def _entity_type(cls):
        """SQL expression for the entity_type hybrid property.

        Allow the use of entity_type in SQL queries by selecting the type of the associated Entity.
        """
        return (
            sa.select(Entity.type)
            .where(Entity.id == cls.entity_id)
            .correlate(cls)
            .scalar_subquery()
        )


class MeasurementKind(Base):
    __tablename__ = "measurement_kind"
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    pref_label: Mapped[str] = mapped_column(index=True)
    structural_domain: Mapped[StructuralDomain | None]
    measurement_annotation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("measurement_annotation.id", ondelete="CASCADE"),
        index=True,
    )
    measurement_annotation: Mapped["MeasurementAnnotation"] = relationship(
        back_populates="measurement_kinds", viewonly=True
    )
    measurement_items: Mapped[list["MeasurementItem"]] = relationship(
        back_populates="measurement_kind", passive_deletes=True
    )
    __table_args__ = (
        UniqueConstraint(
            "measurement_annotation_id",
            "pref_label",
            "structural_domain",
            name=f"uq_{__tablename__}_measurement_annotation_id",
            postgresql_nulls_not_distinct=True,
        ),
    )


class MeasurementItem(Base):
    __tablename__ = "measurement_item"
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[MeasurementStatistic]
    unit: Mapped[MeasurementUnit]
    value: Mapped[float] = mapped_column(index=True)
    measurement_kind_id: Mapped[int] = mapped_column(
        ForeignKey("measurement_kind.id", ondelete="CASCADE"), index=True
    )
    measurement_kind: Mapped["MeasurementKind"] = relationship(
        back_populates="measurement_items", viewonly=True
    )
    __table_args__ = (
        UniqueConstraint(
            "measurement_kind_id",
            "name",
            name=f"uq_{__tablename__}_measurement_kind_id",
            postgresql_nulls_not_distinct=True,
        ),
    )


class Role(LegacyMixin, Identifiable):
    __tablename__ = "role"
    name: Mapped[str] = mapped_column(unique=True, index=True)
    role_id: Mapped[str] = mapped_column(unique=True, index=True)


class ElectricalRecordingStimulus(Entity):
    __tablename__ = EntityType.electrical_recording_stimulus.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)

    name: Mapped[str]
    description: Mapped[str] = mapped_column(default="")

    dt: Mapped[float | None]
    injection_type: Mapped[ElectricalRecordingStimulusType]
    shape: Mapped[ElectricalRecordingStimulusShape]
    start_time: Mapped[float | None]
    end_time: Mapped[float | None]

    recording_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("electrical_cell_recording.id"),
        index=True,
    )

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class ElectricalCellRecording(
    NameDescriptionVectorMixin,
    LocationMixin,
    SubjectMixin,
    LicensedMixin,
    Entity,
):
    __tablename__ = EntityType.electrical_cell_recording.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    recording_type: Mapped[ElectricalRecordingType]
    recording_origin: Mapped[ElectricalRecordingOrigin]
    recording_location: Mapped[STRING_LIST]
    ljp: Mapped[float] = mapped_column(default=0.0)
    comment: Mapped[str] = mapped_column(default="")

    stimuli: Mapped[list[ElectricalRecordingStimulus]] = relationship(
        uselist=True,
        foreign_keys="ElectricalRecordingStimulus.recording_id",
    )

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class SingleNeuronSynaptome(LocationMixin, NameDescriptionVectorMixin, Entity):
    __tablename__ = EntityType.single_neuron_synaptome.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    seed: Mapped[int]
    me_model_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{EntityType.memodel}.id"), index=True
    )
    me_model = relationship("MEModel", uselist=False, foreign_keys=[me_model_id])
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class SingleNeuronSimulation(LocationMixin, NameDescriptionVectorMixin, Entity):
    __tablename__ = EntityType.single_neuron_simulation.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    seed: Mapped[int]
    injection_location: Mapped[STRING_LIST] = mapped_column(default=[])
    recording_location: Mapped[STRING_LIST] = mapped_column(default=[])
    status: Mapped[SingleNeuronSimulationStatus]
    # TODO: called used ?
    me_model_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{EntityType.memodel}.id"), index=True
    )
    me_model = relationship("MEModel", uselist=False, foreign_keys=[me_model_id])
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class SingleNeuronSynaptomeSimulation(LocationMixin, NameDescriptionVectorMixin, Entity):
    __tablename__ = EntityType.single_neuron_synaptome_simulation.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    seed: Mapped[int]
    injection_location: Mapped[STRING_LIST] = mapped_column(default=[])
    recording_location: Mapped[STRING_LIST] = mapped_column(default=[])
    status: Mapped[SingleNeuronSimulationStatus]
    synaptome_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{EntityType.single_neuron_synaptome}.id"), index=True
    )
    synaptome = relationship("SingleNeuronSynaptome", uselist=False, foreign_keys=[synaptome_id])
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class Measurement(Base):
    __tablename__ = "measurement_record"

    id: Mapped[BIGINT] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[MeasurementStatistic]
    unit: Mapped[MeasurementUnit]
    value: Mapped[float]
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), index=True)


class MeasurementsMixin:
    @declared_attr
    @classmethod
    def measurements(cls):
        return relationship(
            "Measurement",
            foreign_keys=Measurement.entity_id,
            uselist=True,
        )


class ExperimentalNeuronDensity(
    NameDescriptionVectorMixin,
    MeasurementsMixin,
    MTypesMixin,
    ETypesMixin,
    LocationMixin,
    SubjectMixin,
    LicensedMixin,
    Entity,
):
    __tablename__ = EntityType.experimental_neuron_density.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class ExperimentalBoutonDensity(
    NameDescriptionVectorMixin,
    MeasurementsMixin,
    MTypesMixin,
    LocationMixin,
    LicensedMixin,
    SubjectMixin,
    Entity,
):
    __tablename__ = EntityType.experimental_bouton_density.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class ExperimentalSynapsesPerConnection(
    NameDescriptionVectorMixin,
    MeasurementsMixin,
    SubjectMixin,
    LocationMixin,
    LicensedMixin,
    Entity,
):
    __tablename__ = EntityType.experimental_synapses_per_connection.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)

    pre_mtype_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mtype_class.id"), index=True)
    pre_mtype: Mapped[MTypeClass] = relationship(uselist=False, foreign_keys=[pre_mtype_id])

    post_mtype_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mtype_class.id"), index=True)
    post_mtype: Mapped[MTypeClass] = relationship(uselist=False, foreign_keys=[post_mtype_id])

    pre_region_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brain_region.id"), index=True)
    pre_region: Mapped[BrainRegion] = relationship(uselist=False, foreign_keys=[pre_region_id])

    post_region_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brain_region.id"), index=True)
    post_region: Mapped[BrainRegion] = relationship(uselist=False, foreign_keys=[post_region_id])

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class Ion(Identifiable):
    __tablename__ = "ion"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=create_uuid)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    ontology_id: Mapped[str | None] = mapped_column(nullable=True, unique=True, index=True)

    @validates("name")
    def _normalize_name(self, key, value):  # noqa: PLR6301, ARG002
        return value.lower() if value else value


class IonChannelModel(NameDescriptionVectorMixin, LocationMixin, SpeciesMixin, Entity):
    __tablename__ = EntityType.ion_channel_model.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)

    is_ljp_corrected: Mapped[bool] = mapped_column(default=False)
    is_temperature_dependent: Mapped[bool] = mapped_column(default=False)
    temperature_celsius: Mapped[int]
    is_stochastic: Mapped[bool] = mapped_column(default=False)
    nmodl_suffix: Mapped[str]
    neuron_block: Mapped[JSON_DICT]

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class IonChannelModelToEModel(Base):
    __tablename__ = "ion_channel_model__emodel"

    ion_channel_model_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{EntityType.ion_channel_model}.id", ondelete="CASCADE"), primary_key=True
    )
    emodel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{EntityType.emodel}.id", ondelete="CASCADE"), primary_key=True
    )


class ValidationResult(Entity):
    __tablename__ = EntityType.validation_result.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    passed: Mapped[bool] = mapped_column(default=False)

    name: Mapped[str] = mapped_column(index=True)

    validated_entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), index=True)
    validated_entity: Mapped[Entity] = relationship(
        "Entity",
        uselist=False,
        foreign_keys=[validated_entity_id],
    )

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
        "inherit_condition": id == Entity.id,
    }


class Asset(Identifiable):
    """Asset table."""

    __tablename__ = "asset"
    status: Mapped[AssetStatus] = mapped_column()
    path: Mapped[str]  # relative path
    full_path: Mapped[str]  # full path on S3
    is_directory: Mapped[bool]
    content_type: Mapped[str]
    size: Mapped[BIGINT]
    sha256_digest: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    meta: Mapped[JSON_DICT]  # not used yet. can be useful?
    label: Mapped[AssetLabel | None]
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


class METypeDensity(
    NameDescriptionVectorMixin, LocationMixin, SpeciesMixin, MTypesMixin, ETypesMixin, Entity
):
    __tablename__ = EntityType.me_type_density
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class BrainAtlas(NameDescriptionVectorMixin, LocationMixin, SpeciesMixin, Entity):
    __tablename__ = EntityType.brain_atlas
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class CellComposition(NameDescriptionVectorMixin, LocationMixin, SpeciesMixin, Entity):
    __tablename__ = EntityType.cell_composition
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012
