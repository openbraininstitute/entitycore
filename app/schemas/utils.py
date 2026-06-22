from typing import Annotated

from pydantic import Field, create_model

from app.schemas.base import Schema

DEFAULT_EXCLUDED_FIELDS = {
    "authorized_public",
}
DEFAULT_PRESERVED_FIELDS = set()


def make_update_schema(
    schema: type[Schema],
    new_schema_name: str | None = None,
    excluded_fields: set = DEFAULT_EXCLUDED_FIELDS,
    preserved_fields: set = DEFAULT_PRESERVED_FIELDS,
):
    """Create a new pydantic schema from current schema where all fields are optional.

    When the api payload instantiates the schema model, the user can explicitly set an update value
    to None.
    """

    def make_optional(field):
        return Annotated[field.annotation | None, Field(default=None)]

    fields = {}
    for name, field in schema.model_fields.items():
        if name in excluded_fields:
            continue

        if name in preserved_fields:
            fields[name] = Annotated[field.annotation, Field(default=field.default)]
            continue

        fields[name] = make_optional(field)

    return create_model(new_schema_name, **fields)  # pyright: ignore reportArgumentType
