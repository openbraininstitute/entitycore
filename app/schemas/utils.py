from typing import Annotated

from pydantic import BaseModel, Field, create_model

EXCLUDED_FIELDS = {
    "authorized_public",
}
PRESERVED_FIELDS = set()


def make_update_schema(
    schema: type[BaseModel],
    new_schema_name: str | None = None,
    excluded_fields: set = EXCLUDED_FIELDS,
    preserved_fields: set = PRESERVED_FIELDS,
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
