from typing import Annotated

from pydantic import ConfigDict, Field, create_model

from app.schemas.base import Schema

DEFAULT_EXCLUDED_FIELDS = {
    "authorized_public",
}
DEFAULT_PRESERVED_FIELDS = set()


class UpdateSchema(Schema):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


def make_update_schema(
    schema: type[Schema],
    new_schema_name: str | None = None,
    excluded_fields: set | None = None,
    preserved_fields: set = DEFAULT_PRESERVED_FIELDS,
):
    """Create a new pydantic schema from current schema where all fields are optional.

    When the api payload instantiates the schema model, the user can explicitly set an update value
    to None.

    ``excluded_fields`` semantics:
    - ``None`` (omitted): use ``DEFAULT_EXCLUDED_FIELDS``
    - empty set: no exclusions (admin opt-out)
    - non-empty set: ``DEFAULT_EXCLUDED_FIELDS | excluded_fields``

    ``preserved_fields``: fields that stay required with their create-schema default instead of
    becoming optional. Useful when a field must not be omitted from the update payload by mistake
    (e.g. ``generation_type`` on cell morphology protocols).
    """

    def make_optional(field):
        return Annotated[field.annotation | None, Field(default=None)]

    if excluded_fields is None:
        excluded = DEFAULT_EXCLUDED_FIELDS
    elif not excluded_fields:
        excluded = set()
    else:
        excluded = DEFAULT_EXCLUDED_FIELDS | excluded_fields

    fields = {}
    for name, field in schema.model_fields.items():
        if name in excluded:
            continue

        if name in preserved_fields:
            fields[name] = Annotated[field.annotation, Field(default=field.default)]
            continue

        fields[name] = make_optional(field)

    return create_model(new_schema_name, __base__=UpdateSchema, **fields)  # pyright: ignore reportArgumentType
