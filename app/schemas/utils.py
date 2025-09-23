from typing import Annotated, Literal

from pydantic import BaseModel, Field, create_model

type NotSet = Literal["<NOT_SET>"]

NOT_SET = "<NOT_SET>"

EXCLUDED_FIELDS = {
    "authorized_public",
}


def make_update_schema(
    schema: type[BaseModel],
    new_schema_name: str | None = None,
    excluded_fields: set = EXCLUDED_FIELDS,
):
    """Create a new pydantic schema from current schema where all fields are optional.

    In order to differentiate between the user providing a None value and an actual not set by the
    user field all fields are by default set to a NOT_SET sentinel.

    When the api payload instantiates the schema model, the user can explicitly set an update value
    to None.

    All attributes with NOT_SET defaults are then removed in the router logic. This way only the
    values set by the user, None included, remain in the update schema.
    """

    def make_optional(field):
        return Annotated[field.annotation | None, Field(default=NOT_SET)]

    fields = {
        name: make_optional(field)
        for name, field in schema.model_fields.items()
        if name not in excluded_fields
    }
    return create_model(new_schema_name, **fields)  # pyright: ignore reportArgumentType
