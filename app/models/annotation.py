from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column, relationship

from app.models.base import Base, LegacyMixin, TimestampMixin, engine


class AnnotationBody(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "annotation_body"
    id = mapped_column(Integer, primary_key=True, index=True, nullable=False, autoincrement=True)
    type = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {
        "polymorphic_identity": "annotation_body",
        "polymorphic_on": type,
    }


class MTypeAnnotationBody(AnnotationBody):
    __tablename__ = "mtype_annotation_body"
    id = Column(
        Integer,
        ForeignKey("annotation_body.id"),
        primary_key=True,
        index=True,
        nullable=False,
        autoincrement=True,
    )
    pref_label = Column(String, unique=True, nullable=False)
    # difficult to believe this can be null
    definition = Column(String, unique=False, nullable=True)
    alt_label = Column(String, unique=False, nullable=True)
    __mapper_args__ = {
        "polymorphic_identity": "mtype_annotation_body",
        "inherit_condition": id == AnnotationBody.id,
    }


class ETypeAnnotationBody(AnnotationBody):
    __tablename__ = "etype_annotation_body"
    id = Column(
        Integer,
        ForeignKey("annotation_body.id"),
        primary_key=True,
        index=True,
        nullable=False,
        autoincrement=True,
    )
    pref_label = Column(String, unique=True, nullable=False)
    definition = Column(String, unique=False, nullable=True)
    alt_label = Column(String, unique=False, nullable=True)
    __mapper_args__ = {
        "polymorphic_identity": "etype_annotation_body",
        "inherit_condition": id == AnnotationBody.id,
    }


class DataMaturityAnnotationBody(AnnotationBody):
    __tablename__ = "datamaturity_annotation_body"
    id = Column(
        Integer,
        ForeignKey("annotation_body.id"),
        primary_key=True,
        index=True,
        nullable=False,
        autoincrement=True,
    )
    pref_label = Column(String, nullable=False, unique=True)
    __mapper_args__ = {
        "polymorphic_identity": "datamaturity_annotation_body",
        "inherit_condition": id == AnnotationBody.id,
    }


class Annotation(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "annotation"
    id = Column(Integer, primary_key=True, index=True)
    annotation_id = Column(String, unique=True)
    note = Column(String, nullable=True)
    entity = relationship("Entity")
    entity_id = Column(Integer, ForeignKey("entity.id"))
    annotation_body_id = Column(Integer, ForeignKey("annotation_body.id"))
    annotation_body = relationship("AnnotationBody", uselist=False)


Base.metadata.create_all(bind=engine)
