from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column

from app.models.base import DistributionMixin
from app.models.entity import Entity


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
