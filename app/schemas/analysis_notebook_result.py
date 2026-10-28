from app.schemas.base import (
    NameDescriptionMixin,
)
from app.schemas.entity import EntityCreate, EntityRead, NestedEntityRead
from app.schemas.utils import make_update_schema


class AnalysisNotebookResultBaseMixin(NameDescriptionMixin):
    pass


class AnalysisNotebookResultCreate(
    AnalysisNotebookResultBaseMixin,
    EntityCreate,
):
    pass


AnalysisNotebookResultUpdate = make_update_schema(
    AnalysisNotebookResultCreate, "AnalysisNotebookResultUpdate"
)  # pyright: ignore [reportInvalidTypeForm]
AnalysisNotebookResultAdminUpdate = make_update_schema(
    AnalysisNotebookResultCreate,
    "AnalysisNotebookResultAdminUpdate",
    excluded_fields=set(),
)  # pyright : ignore [reportInvalidTypeForm]


class NestedAnalysisNotebookResultRead(
    AnalysisNotebookResultBaseMixin,
    NestedEntityRead,
):
    pass


class AnalysisNotebookResultRead(
    AnalysisNotebookResultBaseMixin,
    EntityRead,
):
    pass
