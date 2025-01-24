from datetime import datetime
from typing import Annotated, ClassVar

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
    or_,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
    relationship,
)
from sqlalchemy.types import VARCHAR, TypeDecorator


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
        return func.strpos(column, value) > 0

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


class Agent(Root, TimestampMixin):
    __tablename__ = "agent"
    id: Mapped[int] = mapped_column(ForeignKey("root.id"), primary_key=True, index=True)
    pref_label: Mapped[str] = mapped_column(unique=True, index=False, nullable=False)
    __mapper_args__ = {
        "polymorphic_identity": "agent",
    }


class Person(Agent):
    __tablename__ = "person"
    id: Mapped[int] = mapped_column(ForeignKey("agent.id"), primary_key=True)
    givenName: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    familyName: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
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
    alternative_name: Mapped[str] = mapped_column(
        unique=False, index=False, nullable=False
    )
    __mapper_args__ = {
        "polymorphic_identity": "organization",
    }


class AnnotationBody(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "annotation_body"
    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, nullable=False, autoincrement=True
    )
    type: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {
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
    __mapper_args__ = {
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
    __mapper_args__ = {
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
    __mapper_args__ = {
        "polymorphic_identity": "datamaturity_annotation_body",
    }


class Annotation(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "annotation"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    note: Mapped[str] = mapped_column(nullable=True)
    entity = relationship("Entity", back_populates="annotations")
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id"))
    annotation_body_id: Mapped[int] = mapped_column(ForeignKey("annotation_body.id"))
    annotation_body = relationship("AnnotationBody", uselist=False)


class Entity(TimestampMixin, Root):
    __tablename__ = "entity"
    id = mapped_column(Integer, ForeignKey("root.id"), primary_key=True)
    # type = Column(String, unique=False, index=False, nullable=False)
    annotations = relationship("Annotation", back_populates="entity")
    # TODO: keep the _ ? put on agent ?
    createdBy = relationship("Agent", uselist=False, foreign_keys="Entity.createdBy_id")
    # TODO: move to mandatory
    createdBy_id = Column(Integer, ForeignKey("agent.id"), nullable=True)
    updatedBy = relationship("Agent", uselist=False, foreign_keys="Entity.updatedBy_id")
    # TODO: move to mandatory
    updatedBy_id = Column(Integer, ForeignKey("agent.id"), nullable=True)
    __mapper_args__ = {
        "polymorphic_identity": "entity",
    }


class AnalysisSoftwareSourceCode(DistributionMixin, Entity):
    __tablename__ = "analysis_software_source_code"
    id = mapped_column(
        Integer,
        ForeignKey("entity.id"),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    # TODO: identify what is mandatory
    branch = Column(String, nullable=False, default="")
    codeRepository = Column(String, nullable=False, default="")
    command = Column(String, nullable=False, default="")
    commit = Column(String, nullable=False, default="")
    # TODO: understand what is this
    # configurationTemplate = Column(String, nullable=False, default="")
    description = Column(String, nullable=False, default="")
    name = Column(String, nullable=False, default="")
    subdirectory = Column(String, nullable=False, default="")
    # TODO: foreign key to entity
    targetEntity = Column(String, nullable=False, default="")
    # TODO: should be enum
    programmingLanguage = Column(String, nullable=False, default="")
    # TODO: should be enum
    runtimePlatform = Column(String, nullable=False, default="")
    version = Column(String, nullable=False, default="")

    __mapper_args__ = {"polymorphic_identity": "analysis_software_source_code"}


class Contribution(TimestampMixin, Base):
    __tablename__ = "contribution"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agent.id"), nullable=False)
    agent = relationship("Agent", uselist=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"), nullable=False)
    role = relationship("Role", uselist=False)
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id"), nullable=False)
    entity = relationship("Entity", uselist=False)
    __table_args__ = (
        UniqueConstraint(
            "entity_id", "role_id", "agent_id", name="unique_contribution_1"
        ),
    )


class EModel(DistributionMixin, SpeciesMixin, LocationMixin, Entity):
    __tablename__ = "emodel"
    id = mapped_column(
        Integer,
        ForeignKey("entity.id"),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    description = Column(String, nullable=False, default="")
    name = Column(String, nullable=False, default="")
    # what is this
    eModel = Column(String, nullable=False, default="")
    # what is this
    eType = Column(String, nullable=False, default="")
    # what is this
    iteration = Column(String, nullable=False, default="")
    score = Column(Float, nullable=False, default=-1)
    seed = Column(Integer, nullable=False, default=-1)

    __mapper_args__ = {"polymorphic_identity": "emodel"}


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
        ForeignKey("brain_region.id"), nullable=False
    )
    brain_region = relationship("BrainRegion", uselist=False)
    __mapper_args__ = {"polymorphic_identity": "mesh"}


class MEModel(DistributionMixin, LocationMixin, Entity):
    __tablename__ = "memodel"
    id = mapped_column(
        Integer,
        ForeignKey("entity.id"),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    description = Column(String, nullable=False, default="")
    name = Column(String, nullable=False, default="")
    status = Column(String, nullable=False, default="")
    validated = Column(Boolean, nullable=False, default=False)
    # TODO: see how it relates to other created by properties
    __mapper_args__ = {"polymorphic_identity": "memodel"}


class ReconstructionMorphology(LicensedMixin, LocationMixin, SpeciesMixin, Entity):
    __tablename__ = "reconstruction_morphology"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    description: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    # name is not unique
    name: Mapped[str] = mapped_column(unique=False, index=True, nullable=False)
    morphology_description_vector = Column(TSVECTOR, nullable=True)
    morphology_feature_annotation = relationship(
        "MorphologyFeatureAnnotation", uselist=False
    )
    __mapper_args__ = {"polymorphic_identity": "reconstruction_morphology"}


class MorphologyFeatureAnnotation(TimestampMixin, Base):
    __tablename__ = "morphology_feature_annotation"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    # name = mapped_column(String, unique=True, index=True, nullable=False)
    # description = mapped_column(String, unique=False, index=False, nullable=False)
    reconstruction_morphology_id: Mapped[int] = mapped_column(
        ForeignKey("reconstruction_morphology.id"), nullable=False, unique=True
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
    measurement_of: Mapped[str] = mapped_column(
        unique=False, index=True, nullable=False
    )
    morphology_feature_annotation_id: Mapped[int] = mapped_column(
        ForeignKey("morphology_feature_annotation.id"), nullable=False
    )
    measurement_serie = relationship("MorphologyMeasurementSerieElement", uselist=True)


class MorphologyMeasurementSerieElement(Base):
    __tablename__ = "measurement_serie_element"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=False, index=False, nullable=True)
    value: Mapped[float] = mapped_column(unique=False, index=False, nullable=True)
    measurement_id: Mapped[int] = mapped_column(
        ForeignKey("measurement.id"), nullable=False
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
    __mapper_args__ = {"polymorphic_identity": "single_cell_experimental_trace"}


class SingleNeuronSynaptome(DistributionMixin, LocationMixin, Entity):
    __tablename__ = "single_neuron_synaptome"
    id = mapped_column(
        Integer,
        ForeignKey("entity.id"),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    description = Column(String, nullable=False, default="")
    name = Column(String, nullable=False, default="")
    seed = Column(Integer, nullable=False, default=-1)
    me_model_id = Column(Integer, ForeignKey("memodel.id"), nullable=False)
    me_model = relationship("MEModel", uselist=False, foreign_keys=[me_model_id])
    __mapper_args__ = {"polymorphic_identity": "single_neuron_synaptome"}


class SingleNeuronSimulation(DistributionMixin, LocationMixin, Entity):
    __tablename__ = "single_neuron_simulation"
    id = mapped_column(
        Integer,
        ForeignKey("entity.id"),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        autoincrement=True,
    )
    description = Column(String, nullable=False, default="")
    name = Column(String, nullable=False, default="")
    seed = Column(Integer, nullable=False, default=-1)
    injectionLocation = Column(StringList, nullable=False, default="")
    recordingLocation = Column(StringList, nullable=False, default=[])
    # TODO: called used ?
    me_model_id = Column(Integer, ForeignKey("memodel.id"), nullable=False)
    me_model = relationship("MEModel", uselist=False, foreign_keys=[me_model_id])
    __mapper_args__ = {"polymorphic_identity": "single_neuron_simulation"}


class ExperimentalNeuronDensity(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "experimental_neuron_density"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(unique=False, index=True, nullable=False)
    description: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "experimental_neuron_density"}


class ExperimentalBoutonDensity(LocationMixin, SpeciesMixin, LicensedMixin, Entity):
    __tablename__ = "experimental_bouton_density"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(unique=False, index=True, nullable=False)
    description: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "experimental_bouton_density"}


class ExperimentalSynapsesPerConnection(
    LocationMixin, SpeciesMixin, LicensedMixin, Entity
):
    __tablename__ = "experimental_synapses_per_connection"
    id: Mapped[int] = mapped_column(ForeignKey("entity.id"), primary_key=True)
    name: Mapped[str] = mapped_column(unique=False, index=True, nullable=False)
    description: Mapped[str] = mapped_column(unique=False, index=False, nullable=False)
    __mapper_args__ = {"polymorphic_identity": "experimental_synapses_per_connection"}
