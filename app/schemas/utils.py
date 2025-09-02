from pydantic import BaseModel, create_model


def make_fields_optional(schema: type[BaseModel], new_schema_name: str) -> type[BaseModel]:
    """Create a new pydantic schema from current schema where all fields are optional."""

    def make_optional(field):
        return field.annotation | None, None  # Defaults are removed when creating optional fields

    fields = {name: make_optional(field) for name, field in schema.model_fields.items()}
    return create_model(new_schema_name, **fields)  # pyright: ignore reportArgumentType
