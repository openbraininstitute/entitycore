from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict

from app.db.types import ActivityType


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ActivityTypeMixin:
    type: ActivityType | None = None


class AuthorizationMixin:
    authorized_project_id: UUID4
    authorized_public: bool = False


class AuthorizationOptionalPublicMixin:
    authorized_public: bool = False


class OptionalProjectContext(Schema):
    virtual_lab_id: UUID4 | None = None
    project_id: UUID4 | None = None


class NameDescriptionMixin:
    name: str
    description: str


class TimestapMixin:
    creation_date: datetime
    update_date: datetime
