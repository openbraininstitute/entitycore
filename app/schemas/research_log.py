from app.schemas.base import AuthorizedProjectIdMixin, NameDescriptionMixin
from app.schemas.entity import EntityCreate, EntityRead
from app.schemas.utils import make_update_schema


class ResearchLogCreate(NameDescriptionMixin, EntityCreate):
    pass


class ResearchLogAdminCreate(AuthorizedProjectIdMixin, ResearchLogCreate):
    pass


ResearchLogUpdate = make_update_schema(ResearchLogCreate, "ResearchLogUpdate")  # pyright: ignore [reportInvalidTypeForm]
ResearchLogAdminUpdate = make_update_schema(
    ResearchLogCreate,
    "ResearchLogAdminUpdate",
    excluded_fields=set(),
)  # pyright: ignore [reportInvalidTypeForm]


class ResearchLogRead(NameDescriptionMixin, EntityRead):
    pass
