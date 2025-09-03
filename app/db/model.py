import uuid
from datetime import datetime, timedelta
from typing import ClassVar
from uuid import UUID

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
    foreign,
    mapped_column,
    relationship,
    validates,
)

from app.db.types import (
    BIGINT,
    JSON_DICT,
    STRING_LIST,
    ActivityType,
    AgentType,
    AgePeriod,
    AnnotationBodyType,
    AssetLabel,
    AssetStatus,
    CircuitBuildCategory,
    CircuitScale,
    ContentType,
    DerivationType,
    ElectricalRecordingOrigin,
    ElectricalRecordingStimulusShape,
    ElectricalRecordingStimulusType,
    ElectricalRecordingType,
    EntityType,
    ExternalSource,
    MeasurementStatistic,
    MeasurementUnit,
    PointLocation,
    PointLocationType,
    PublicationType,
    Sex,
    SimulationExecutionStatus,
    SingleNeuronSimulationStatus,
    StorageType,
    StructuralDomain,
    ValidationStatus,
)
from app.schemas.publication import Author
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

    @declared_attr
    @classmethod
    def created_by_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(ForeignKey("agent.id"), index=True)

    @declared_attr
    @classmethod
    def created_by(cls) -> Mapped["Agent"]:
        return relationship(
            "Agent",
            # needed to enforce the correct direction of joins in Agent-derived tables
            primaryjoin=lambda: cls.created_by_id == foreign(Agent.id),
            uselist=False,
            viewonly=True,
        )

    @declared_attr
    @classmethod
    def updated_by_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(ForeignKey("agent.id"), index=True)

    @declared_attr
    @classmethod
    def updated_by(cls) -> Mapped["Agent"]:
        return relationship(
            "Agent",
            # needed to enforce the correct direction of joins in Agent-derived tables
            primaryjoin=lambda: cls.updated_by_id == foreign(Agent.id),
            uselist=False,
            viewonly=True,
        )


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


class License(LegacyMixin, Identifiable, NameDescriptionVectorMixin):
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
    pref_label: Mapped[str] = mapped_column(index=True)
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


class Organization(Agent):
    __tablename__ = AgentType.organization.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent.id"), primary_key=True)
    # what is the difference between name and label here ?
    alternative_name: Mapped[str]

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
        "polymorphic_load": "selectin",
    }


class Consortium(Agent):
    __tablename__ = AgentType.consortium.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent.id"), primary_key=True)
    # what is the difference between name and label here ?
    alternative_name: Mapped[str]

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
        "polymorphic_load": "selectin",
    }


class Usage(Base):
    __tablename__ = "usage"
    usage_entity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("entity.id", ondelete="CASCADE"),
        primary_key=True,
    )
    usage_activity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activity.id", ondelete="CASCADE"), primary_key=True
    )


class Generation(Base):
    __tablename__ = "generation"
    generation_entity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("entity.id", ondelete="CASCADE"), primary_key=True
    )
    generation_activity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activity.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Activity(Identifiable):
    """Represents a base class for activities in the system.

    see https://www.w3.org/TR/prov-dm/#term-Activity
    Attributes:
        type (ActivityType): The type of the activity.
        start_time: The start time of the activity, or None if not set.
        end_time: The end time of the activity, or None if not set.
        used_ids: List of UUIDs referencing entities used by this activity.
        used: List of Entity objects used by this activity (view only).
        generated_ids: List of UUIDs referencing entities generated by this activity.
        generated: List of Entity objects generated by this activity (view only).
    """

    __tablename__ = "activity"

    authorized_project_id: Mapped[uuid.UUID]
    authorized_public: Mapped[bool] = mapped_column(default=False)
    type: Mapped[ActivityType]
    start_time: Mapped[datetime | None]
    end_time: Mapped[datetime | None]
    used: Mapped[list["Entity"]] = relationship(
        "Entity",
        secondary="usage",
        secondaryjoin="Entity.id == usage.c.usage_entity_id",
        primaryjoin="Activity.id == usage.c.usage_activity_id",
        uselist=True,
        passive_deletes=True,  # let ORM perform cascade deletes
    )
    generated: Mapped[list["Entity"]] = relationship(
        "Entity",
        secondary="generation",
        secondaryjoin="Entity.id == generation.c.generation_entity_id",
        primaryjoin="Activity.id == generation.c.generation_activity_id",
        uselist=True,
        passive_deletes=True,  # let ORM perform cascade deletes
    )
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
        "polymorphic_on": "type",
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


class MTypeClass(AnnotationMixin, LegacyMixin, Identifiable):
    __tablename__ = "mtype_class"


class ETypeClass(AnnotationMixin, LegacyMixin, Identifiable):
    __tablename__ = "etype_class"


class MTypeClassification(Identifiable):
    __tablename__ = "mtype_classification"

    authorized_project_id: Mapped[uuid.UUID]
    authorized_public: Mapped[bool] = mapped_column(default=False)

    mtype_class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mtype_class.id"), index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), index=True)

    __table_args__ = (UniqueConstraint("entity_id", "mtype_class_id", name="uq_mtype_per_entity"),)


class ETypeClassification(Identifiable):
    __tablename__ = "etype_classification"

    authorized_project_id: Mapped[uuid.UUID]
    authorized_public: Mapped[bool] = mapped_column(default=False)

    etype_class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("etype_class.id"), index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), index=True)

    __table_args__ = (UniqueConstraint("entity_id", "etype_class_id", name="uq_etype_per_entity"),)


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


class Entity(LegacyMixin, Identifiable):
    __tablename__ = "entity"

    type: Mapped[EntityType]
    annotations = relationship("Annotation", back_populates="entity")

    authorized_project_id: Mapped[uuid.UUID]
    authorized_public: Mapped[bool] = mapped_column(default=False)

    contributions: Mapped[list["Contribution"]] = relationship(uselist=True, viewonly=True)
    assets: Mapped[list["Asset"]] = relationship(
        "Asset",
        uselist=True,
        viewonly=True,
        primaryjoin=lambda: sa.and_(
            Entity.id == Asset.entity_id, Asset.status != AssetStatus.DELETED
        ),
    )

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
        "polymorphic_on": "type",
    }


class Subject(NameDescriptionVectorMixin, SpeciesMixin, Entity):
    __tablename__ = EntityType.subject.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    age_value: Mapped[timedelta | None]
    age_min: Mapped[timedelta | None]
    age_max: Mapped[timedelta | None]
    age_period: Mapped[AgePeriod | None]
    sex: Mapped[Sex]
    weight: Mapped[float | None]  # in grams

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class SubjectMixin:
    subject_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("subject.id"), index=True)

    @declared_attr
    @classmethod
    def subject(cls):
        return relationship("Subject", uselist=False, foreign_keys=cls.subject_id)


class Publication(Identifiable):
    """Represents a scientific publication entity in the database.

    Attributes:
        id (uuid.UUID): Primary key.
        DOI (str): Digital Object Identifier for the publication.
        title (str | None): Title of the publication.
        authors (list[Author] | None): List of authors associated with the publication.
        publication_year (int | None): Year the publication was released.
        abstract (str | None): Abstract or summary of the publication.

    """

    __tablename__ = EntityType.publication.value
    DOI: Mapped[str] = mapped_column()  # explicit for the case insensitive index
    title: Mapped[str | None]
    authors: Mapped[list[Author] | None] = mapped_column(JSONB)
    publication_year: Mapped[int | None]
    abstract: Mapped[str | None]

    __table_args__ = (Index("ix_publication_doi_normalized", func.lower(DOI), unique=True),)


class ExternalUrl(Identifiable, NameDescriptionVectorMixin):
    """Represents a web page on an external data source.

    Attributes:
        id (uuid.UUID): Primary key.
        source (ExternalSource): Name of the external data source, e.g. channelpedia.
        url (str): URL of the webpage, e.g. "https://channelpedia.epfl.ch/wikipages/189".
    """

    __tablename__ = EntityType.external_url.value
    source: Mapped[ExternalSource]
    url: Mapped[str] = mapped_column(String, index=True, unique=True)


class ScientificArtifact(Entity, SubjectMixin, LocationMixin, LicensedMixin):
    """Represents a scientific artifact entity in the database.

    Attributes:
        __tablename__ (str): Name of the database table for scientific artifacts.
        id (uuid.UUID): Primary key, references the base entity ID.
        experiment_date (datetime | None): Date of the experiment associated with the artifact.
        contact_email (str | None): Optional string of a contact person's e-mail address.
        published_in (str | None): Optional string with short version of the source publication(s).

    Mapper Args:
        polymorphic_identity (str): Used for SQLAlchemy polymorphic inheritance.
    """

    __tablename__ = EntityType.scientific_artifact.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)

    experiment_date: Mapped[datetime | None]
    contact_email: Mapped[str | None]
    published_in: Mapped[str | None]

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
        "polymorphic_on": "type",
    }


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
    agent = relationship("Agent", uselist=False, foreign_keys=agent_id)
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

    emodel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{EntityType.emodel}.id"))

    emodel = relationship("EModel", foreign_keys=[emodel_id], uselist=False)

    calibration_result = relationship(
        "MEModelCalibrationResult",
        uselist=False,
        foreign_keys="MEModelCalibrationResult.calibrated_entity_id",
        lazy="joined",
    )

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


class ElectricalRecordingStimulus(Entity, NameDescriptionVectorMixin):
    __tablename__ = EntityType.electrical_recording_stimulus.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)

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
    ScientificArtifact,
    NameDescriptionVectorMixin,
    ETypesMixin,
):
    __tablename__ = EntityType.electrical_cell_recording.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scientific_artifact.id"), primary_key=True)
    recording_type: Mapped[ElectricalRecordingType]
    recording_origin: Mapped[ElectricalRecordingOrigin]
    recording_location: Mapped[STRING_LIST]
    ljp: Mapped[float] = mapped_column(default=0.0)
    temperature: Mapped[float | None]
    comment: Mapped[str] = mapped_column(default="")

    stimuli: Mapped[list[ElectricalRecordingStimulus]] = relationship(
        uselist=True,
        foreign_keys="ElectricalRecordingStimulus.recording_id",
    )

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class IonChannel(NameDescriptionVectorMixin, Identifiable):
    __tablename__ = "ion_channel"

    label: Mapped[str]
    gene: Mapped[str]
    synonyms: Mapped[STRING_LIST]

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class IonChannelRecording(ElectricalCellRecording):
    __tablename__ = EntityType.ion_channel_recording.value

    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("electrical_cell_recording.id"), primary_key=True
    )
    ion_channel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ion_channel.id"),
        index=True,
    )
    ion_channel: Mapped[IonChannel] = relationship(
        "IonChannel",
        uselist=False,
        foreign_keys=[ion_channel_id],
    )
    cell_line: Mapped[str]

    # Fixes sqlalchemy.exc.ArgumentError:
    # Index 'ix_ion_channel_recording_description_vector'
    # is against table 'electrical_cell_recording',
    # and cannot be associated with table 'ion_channel_recording'.
    __table_args__ = ()  # type: ignore[reportAssignmentType]

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


class IonChannelModel(NameDescriptionVectorMixin, ScientificArtifact):
    __tablename__ = EntityType.ion_channel_model.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scientific_artifact.id"), primary_key=True)

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


class MEModelCalibrationResult(Entity):
    __tablename__ = EntityType.memodel_calibration_result.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    holding_current: Mapped[float]
    threshold_current: Mapped[float]
    rin: Mapped[float | None]
    calibrated_entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("memodel.id"), index=True)
    calibrated_entity: Mapped[Entity] = relationship(
        "MEModel",
        uselist=False,
        foreign_keys=[calibrated_entity_id],
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
    content_type: Mapped[ContentType] = mapped_column(
        sa.Enum(ContentType, values_callable=lambda x: [i.value for i in x])
    )
    size: Mapped[BIGINT]
    sha256_digest: Mapped[bytes | None] = mapped_column(LargeBinary(32))
    meta: Mapped[JSON_DICT]  # not used yet. can be useful?
    label: Mapped[AssetLabel]
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), index=True)
    storage_type: Mapped[StorageType]

    # partial unique index
    __table_args__ = (
        Index(
            "ix_asset_full_path",
            "full_path",
            unique=True,
            postgresql_where=(status != AssetStatus.DELETED.name),
        ),
        Index(
            "uq_asset_entity_id_path",
            "path",
            "entity_id",
            unique=True,
            postgresql_where=(status != AssetStatus.DELETED.name),
        ),
    )


class METypeDensity(
    NameDescriptionVectorMixin, LocationMixin, SpeciesMixin, MTypesMixin, ETypesMixin, Entity
):
    __tablename__ = EntityType.me_type_density.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class BrainAtlas(NameDescriptionVectorMixin, SpeciesMixin, Entity):
    __tablename__ = EntityType.brain_atlas.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)

    hierarchy_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brain_region_hierarchy.id"), index=True
    )

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class BrainAtlasRegion(Entity, LocationMixin):
    __tablename__ = EntityType.brain_atlas_region.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)

    # only the volume for leaf nodes is saved; the consumer must calculate
    # volumes depending on which view of the hierarchy they are using
    volume: Mapped[float | None]
    is_leaf_region: Mapped[bool] = mapped_column(default=False)

    brain_atlas_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brain_atlas.id"), index=True)

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class CellComposition(NameDescriptionVectorMixin, LocationMixin, SpeciesMixin, Entity):
    __tablename__ = EntityType.cell_composition.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class SimulationCampaign(
    NameDescriptionVectorMixin,
    Entity,
):
    """Represents a simulation campaign entity in the database.

    A simulation campaign represents the specification of a set of simulations.

    it has an asset which is the simulation campaign configuration file.

    Attributes:
        id (uuid.UUID): Primary key for the simulation campaign, referencing the entity ID.
    """

    __tablename__ = EntityType.simulation_campaign.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)

    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), index=True)

    simulations = relationship(
        "Simulation",
        uselist=True,
        back_populates="simulation_campaign",
        foreign_keys="Simulation.simulation_campaign_id",
    )
    scan_parameters: Mapped[JSON_DICT] = mapped_column(
        default={},
        nullable=False,
        server_default="{}",
    )
    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
        "inherit_condition": id == Entity.id,
    }


class Simulation(Entity, NameDescriptionVectorMixin):
    """Represents a simulation entity in the database.

    It represents the definition / configuration of a simulation. It has an asset which is
    the SONATA simulation configuration file.

    Attributes:
        id (uuid.UUID): Primary key for the simulation, referencing the entity ID.
        simulation_campaign_id (uuid.UUID): Foreign key referencing the simulation campaign ID.
        simulation_campaign (SimulationCampaign): The simulation campaign this simulation
          belongs to.
        entity_id (uuid.UUID): Foreign key referencing the entity ID.
        entity (Entity): The entity this simulation is associated with.
        scan_parameters (JSON_DICT): Scan parameters for the simulation.
    """

    __tablename__ = EntityType.simulation.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    simulation_campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("simulation_campaign.id"), index=True
    )
    simulation_campaign: Mapped[SimulationCampaign] = relationship(
        "SimulationCampaign",
        uselist=False,
        foreign_keys=[simulation_campaign_id],
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), index=True)
    entity: Mapped[Entity] = relationship(
        "Entity",
        uselist=False,
        foreign_keys=[entity_id],
    )
    scan_parameters: Mapped[JSON_DICT] = mapped_column(
        default={},
        nullable=False,
        server_default="{}",
    )

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
        "inherit_condition": id == Entity.id,
    }


class SimulationExecution(Activity):
    """Represents the execution of a simulation.

    It stores the execution status of a simulation.

    Attributes:
        id (uuid.UUID): Primary key for the simulation execution, referencing the entity ID.
        status (SimulationExecutionStatus): The status of the simulation execution.
    """

    __tablename__ = ActivityType.simulation_execution.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activity.id"), primary_key=True)
    status: Mapped[SimulationExecutionStatus] = mapped_column(
        Enum(SimulationExecutionStatus, name="simulation_execution_status"),
        default=SimulationExecutionStatus.created,
    )

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class SimulationResult(Entity, NameDescriptionVectorMixin):
    """Represents the results generated by the execution of a simulation.

    it has a directory asset which in the SONATA format.

    Attributes:
        id (uuid.UUID): Primary key for the simulation result.
    """

    __tablename__ = EntityType.simulation_result.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)

    simulation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("simulation.id"), index=True)

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class SimulationGeneration(Activity):
    """Represents a simulation generation activity in the database.

    A simulation generation activity is responsible for generating the configuration files for each
    simulation part of a simulation campaign.

    Attributes:
        id (uuid.UUID): Primary key for the simulation generation, referencing the activity ID.
    """

    __tablename__ = ActivityType.simulation_generation.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activity.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012


class Validation(Activity):
    __tablename__ = ActivityType.validation.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activity.id"), primary_key=True)

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
        "polymorphic_on": "type",
    }


class Calibration(Activity):
    __tablename__ = ActivityType.calibration.value

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activity.id"), primary_key=True)

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_identity": __tablename__,
        "polymorphic_on": "type",
    }


class Derivation(Base):
    __tablename__ = "derivation"
    used_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    generated_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    used: Mapped["Entity"] = relationship(foreign_keys=[used_id])
    generated: Mapped["Entity"] = relationship(foreign_keys=[generated_id])
    derivation_type: Mapped[DerivationType | None]


class ScientificArtifactPublicationLink(Identifiable):
    """Represents the association between a scientific artifact and a publication in the database.

    This model links a scientific artifact to a publication, specifying the type of publication.
    It enforces uniqueness on the combination of publication and scientific artifact, ensuring that
    each artifact-publication pair is unique. The publication type determines if the artefact was
    used by the publication, or if the publication is used to generate the artifact or if the
    artefact is a result of the publication.

    Attributes:
        publication_id (UUID): Foreign key referencing the associated publication.
        publication_type (PublicationType): Enum indicating the nature of the relationship.
        scientific_artifact_id (UUID): Foreign key referencing the associated scientific artifact.
        publication (Publication): Relationship to the Publication model.
        scientific_artifact (ScientificArtifact): Relationship to the ScientificArtifact model.

    Table:
        Unique constraint on (publication_id, scientific_artifact_id).
    """

    __tablename__ = "scientific_artifact_publication_link"
    publication_id: Mapped[UUID] = mapped_column(ForeignKey("publication.id"), index=True)
    publication_type: Mapped[PublicationType]
    scientific_artifact_id: Mapped[UUID] = mapped_column(
        ForeignKey("scientific_artifact.id"), index=True
    )

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
    )


class ScientificArtifactExternalUrlLink(Identifiable):
    """Represents the association between a scientific artifact and an external url.

    It enforces uniqueness on the combination of external url and scientific artifact,
    ensuring that each (scientific_artifact, external_url) pair is unique.

    Attributes:
        external_url_id (UUID): Foreign key referencing the associated external url.
        scientific_artifact_id (UUID): Foreign key referencing the associated scientific artifact.
        external_url (ExternalUrl): Relationship to the ExternalUrl model.
        scientific_artifact (ScientificArtifact): Relationship to the ScientificArtifact model.

    Table:
        Unique constraint on (external_url_id, scientific_artifact_id).
    """

    __tablename__ = "scientific_artifact_external_url_link"
    external_url_id: Mapped[UUID] = mapped_column(ForeignKey("external_url.id"), index=True)
    scientific_artifact_id: Mapped[UUID] = mapped_column(
        ForeignKey("scientific_artifact.id"), index=True
    )

    external_url: Mapped["ExternalUrl"] = relationship(
        "ExternalUrl",
        foreign_keys=[external_url_id],
        uselist=False,
    )
    scientific_artifact: Mapped["ScientificArtifact"] = relationship(
        "ScientificArtifact",
        foreign_keys=[scientific_artifact_id],
        uselist=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "external_url_id",
            "scientific_artifact_id",
            name="uq_scientific_artifact_external_url_link",
        ),
    )


class Circuit(ScientificArtifact, NameDescriptionVectorMixin):
    """Represents a neural circuit as a scientific artifact.

       It can be a single neuron up to a whole brain model.

    Attributes:
        id (uuid.UUID): Primary key.
        root_circuit_id (uuid.UUID | None): Optional reference to the root circuit
            (self-referential).
        root_circuit (Circuit | None): Relationship to the root Circuit instance. A root
            circuit does not derive from another circuit.
        atlas_id (uuid.UUID | None): Optional reference to the associated BrainAtlas.
        atlas (BrainAtlas | None): Relationship to the BrainAtlas instance.
        build_category (CircuitBuildCategory): Category describing how the circuit was built.
        scale (CircuitScale): Scale of the circuit (e.g., microcircuit, mesocircuit).
        has_morphologies (bool): Indicates if the circuit includes morphologies.
        has_point_neurons (bool): Indicates if the circuit includes point neurons.
        has_electrical_cell_models (bool): Indicates if the circuit includes electrical cell models.
        has_spines (bool): Indicates if the circuit includes spines.
        number_neurons (int): Number of neurons in the circuit.
        number_synapses (int): Number of synapses in the circuit.
        number_connections (int | None): Number of connections in the circuit, if available.

    Notes:
        - Inherits additional attributes from ScientificArtifact (e.g., name, description,
          brain_region).
        - References to assets such as SONATA circuit folders, connectivity matrices,
          figures, and statistics.
        - Asset: folder containing SONATA circuit files.
    """

    __tablename__ = EntityType.circuit.value
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scientific_artifact.id"), primary_key=True)

    # Still missing:
    # - connectivity_matrices: Folder containing multiple .h5 files in ConnectomeUtilities format
    # - circuit_figures: Folder containing all pre-computed overview figures
    # - circuit_statistics: Folder containing all pre-computed circuit statistics

    root_circuit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("circuit.id"), index=True)
    atlas_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("brain_atlas.id"), index=True)

    build_category: Mapped[CircuitBuildCategory]
    scale: Mapped[CircuitScale]

    has_morphologies: Mapped[bool]
    has_point_neurons: Mapped[bool]
    has_electrical_cell_models: Mapped[bool]
    has_spines: Mapped[bool]

    number_neurons: Mapped[int] = mapped_column(BigInteger)
    number_synapses: Mapped[int] = mapped_column(BigInteger)
    number_connections: Mapped[int | None] = mapped_column(BigInteger)

    # To be added later:
    # version: Mapped[str] = mapped_column(default="")

    # building_workflow_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("building_workflow.id")
    # , index=True, nullable=False, default=None)
    # building_workflow: Mapped[BuildingWorkflow] = relationship("BuildingWorkflow", uselist=False,i
    #  foreign_keys=[building_workflow_id])

    # flatmap_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("flatmap.id"), index=True,i
    #  nullable=True, default=None)
    # flatmap: Mapped[FlatMap] = relationship("FlatMap", uselist=False, foreign_keys=[flatmap_id])

    # calibration_data (multiple entities): ...

    __mapper_args__ = {"polymorphic_identity": __tablename__}  # noqa: RUF012
