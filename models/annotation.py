from models.base import TimestampMixin, LegacyMixin, Base, engine
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import mapped_column, relationship


class AnnotationBody(TimestampMixin, Base):
    __tablename__ = "annotation_body"
    id = mapped_column(Integer, primary_key=True, index=True)
    type = Column(String, unique=False, index=False, nullable=False)
    __mapper_args__ = {
        "polymorphic_identity": "annotation_body",
        "polymorphic_on": type,
    }


class MTypeAnnotationBody(TimestampMixin, Base):
    __tablename__ = "mtype_annotation_body"
    id = mapped_column(Integer, primary_key=True, index=True)
    label = Column(String, nullable=False)
    __table_args__ = (
        UniqueConstraint("label", name="unique_mtype_annotation_label_1"),
    )
    __mapper_args__ = {"polymorphic_identity": "mtype_annotation_body"}


# class DataQualityAnnotationBody(TimestampMixin, Base):
#     __tablename__ = "dataquality_annotation_body"
#     id = mapped_column(Integer, primary_key=True, index=True)
#     label = Column(String, nullable=False)
#     __table_args__ = (
#         UniqueConstraint("label", name="unique_dataquality_annotation_label_1"),
#     )
#     __mapper_args__ = {"polymorphic_identity": "dataquality_annotation_body"}


class DataMaturityAnnotationBody(TimestampMixin, Base):
    __tablename__ = "datamaturity_annotation_body"
    id = mapped_column(Integer, primary_key=True, index=True)
    label = Column(String, nullable=False)
    __table_args__ = (
        UniqueConstraint("label", name="unique_datamaturity_annotation_label_1"),
    )
    __mapper_args__ = {"polymorphic_identity": "datamaturity_annotation_body"}


class Annotation(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "annotation"
    id = Column(Integer, primary_key=True, index=True)
    annotation_id = mapped_column(String, unique=True)
    note = Column(String, nullable=True)
    entity = relationship("Entity")
    entity_id = Column(Integer, ForeignKey("entity.id"))
    annotation_body_id = Column(Integer, ForeignKey("annotation_body.id"))
    annotation_body = relationship("AnnotationBody", uselist=False)


Base.metadata.create_all(bind=engine)
