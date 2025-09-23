from pydantic import BaseModel, ConfigDict

from app.schemas.agent import CreatedByUpdatedByMixin
from app.schemas.asset import AssetsMixin
from app.schemas.base import (
    AuthorizationMixin,
    AuthorizationOptionalPublicMixin,
    CreationMixin,
    EntityTypeMixin,
    IdentifiableMixin,
)
from app.schemas.utils import make_update_schema


class AnalysisNotebookResultBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str


class AnalysisNotebookResultCreate(
    AnalysisNotebookResultBase,
    AuthorizationOptionalPublicMixin,
):
    pass


AnalysisNotebookResultUpdate = make_update_schema(
    AnalysisNotebookResultCreate, "AnalysisNotebookResultUpdate"
)  # pyright: ignore [reportInvalidTypeForm]


class NestedAnalysisNotebookResultRead(
    AnalysisNotebookResultBase,
    EntityTypeMixin,
    IdentifiableMixin,
):
    pass


class AnalysisNotebookResultRead(
    NestedAnalysisNotebookResultRead,
    AssetsMixin,
    CreatedByUpdatedByMixin,
    CreationMixin,
    AuthorizationMixin,
):
    pass
