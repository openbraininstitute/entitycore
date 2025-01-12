from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped

from app.models.base import Base, LegacyMixin, TimestampMixin


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


# class AnnotatedMixin:
#     annotations = relationship("Annotation", uselist=True, back_populates="entity")


class Annotation(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "annotation"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    note: Mapped[str] = mapped_column(nullable=True)
    entity = relationship("Entity", back_populates="annotations")
    entity_id: Mapped[int] = mapped_column(ForeignKey("entity.id"))
    annotation_body_id: Mapped[int] = mapped_column(ForeignKey("annotation_body.id"))
    annotation_body = relationship("AnnotationBody", uselist=False)
