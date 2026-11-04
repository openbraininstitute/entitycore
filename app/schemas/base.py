from collections.abc import Callable
from datetime import datetime
from typing import Any, ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from app.db.types import ActivityType
from app.schemas.expand import ExpandableField, collect_expandable_fields, validate_loaded


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # field name -> expandable field, collected at class creation (see app.schemas.expand)
    __expandable_fields__: ClassVar[dict[str, ExpandableField]] = {}

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:  # ruff:ignore[bad-dunder-method-name]
        """Collect and check the expandable fields of the class."""
        super().__pydantic_init_subclass__(**kwargs)
        cls.__expandable_fields__ = collect_expandable_fields(cls)
        if cls.__expandable_fields__ and not issubclass(cls, ExpandableSchema):
            msg = f"{cls.__name__} has expandable fields and must inherit from ExpandableSchema"
            raise TypeError(msg)


class ExpandableSchema(Schema):
    """Base class of the schemas with expandable fields (see `app.schemas.expand.Expandable`).

    When validated from an ORM instance, an expandable field is set only if its attribute is
    loaded, and it is omitted from the output otherwise. An attribute can also be loaded without
    being requested, e.g. if the instance was already loaded in the same session.
    """

    @model_validator(mode="wrap")
    @classmethod
    def _skip_unloaded_expandable_fields(cls, data: Any, handler: Callable[[Any], Any]) -> Any:
        return validate_loaded(cls.__expandable_fields__, data, handler)


class ActivityTypeMixin:
    type: ActivityType | None = None


class AuthorizationMixin:
    authorized_project_id: UUID
    authorized_public: bool = False


class AuthorizationOptionalPublicMixin:
    authorized_public: bool = False


class OptionalProjectContext(Schema):
    virtual_lab_id: UUID | None = None
    project_id: UUID | None = None


class NameDescriptionMixin:
    name: str
    description: str


class TimestapMixin:
    creation_date: datetime
    update_date: datetime
