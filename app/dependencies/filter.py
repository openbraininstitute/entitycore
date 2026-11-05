from copy import deepcopy
from typing import Any, get_args, get_origin

from fastapi import Depends, Query, params
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError, create_model
from pydantic.fields import FieldInfo

from app.filters.base import (
    NESTED_SEPARATOR,
    CustomFilter,
    nested_filter_type,
    nested_prefix,
)


def _order_by_schema_extra(fields: list[str]) -> dict[str, Any]:
    """Return a json_schema_extra dict that injects all valid order_by values as enum.

    Each field is expanded to unprefixed (ascending), `+` (ascending), and `-` (descending).
    """
    return {
        "items": {
            "type": "string",
            "enum": [f"{p}{f}" for p in ("", "+", "-") for f in fields],
        }
    }


def _is_list_type(annotation: Any) -> bool:
    if annotation is list or get_origin(annotation) is list:
        return True
    return any(get_origin(arg) is list for arg in get_args(annotation))


def _as_query_field(
    field: FieldInfo, json_schema_extra: dict[str, Any] | None = None
) -> tuple[Any, FieldInfo]:
    """Wrap list defaults in `Query`, otherwise FastAPI reads list fields from the body."""
    info = deepcopy(field)
    if _is_list_type(field.annotation) and type(info.default) is not params.Query:
        info.default = Query(default=info.default, json_schema_extra=json_schema_extra)
    return field.annotation, info


def _flatten_fields(
    filter_model: type[CustomFilter],
    *,
    prefix: str = "",
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Expand nested filters into flat query fields prefixed by their field name or `Prefix`.

    Parent prefixes are not accumulated.
    """
    ordering_fields: list[str] | None = getattr(
        filter_model.Constants, "ordering_model_fields", None
    )
    ordering_field = filter_model.Constants.ordering_field_name
    if fields is None:
        fields = {}

    for name, field in filter_model.model_fields.items():
        nested = nested_filter_type(field.annotation)
        if nested is not None:
            abs_prefix = nested_prefix(name, field)
            _flatten_fields(nested, prefix=f"{abs_prefix}{NESTED_SEPARATOR}", fields=fields)
            continue

        if prefix and name == ordering_field:
            continue

        flat = f"{prefix}{name}"
        if flat in fields:
            msg = f"Duplicate query parameter {flat!r} in {filter_model.__name__}"
            raise ValueError(msg)
        json_schema_extra = (
            _order_by_schema_extra(ordering_fields)
            if name == ordering_field and ordering_fields
            else None
        )
        fields[flat] = _as_query_field(field, json_schema_extra)

    return fields


def _unflatten(
    filter_model: type[CustomFilter], data: dict[str, Any], *, prefix: str = ""
) -> CustomFilter:
    ordering_field = filter_model.Constants.ordering_field_name
    kwargs: dict[str, Any] = {}

    for name, field in filter_model.model_fields.items():
        nested = nested_filter_type(field.annotation)
        if nested is not None:
            abs_prefix = nested_prefix(name, field)
            kwargs[name] = _unflatten(nested, data, prefix=f"{abs_prefix}{NESTED_SEPARATOR}")
            continue

        if prefix and name == ordering_field:
            continue

        flat = f"{prefix}{name}"
        if flat in data:
            kwargs[name] = data[flat]

    return filter_model(**kwargs)


def FilterDepends(filter_model: type[CustomFilter], *, by_alias: bool = False, **_) -> Any:
    """Return a FastAPI dependency that parses query parameters into a filter model instance.

    Nested filters are exposed as flat query params prefixed by their field name or `Prefix`.
    """
    fields = _flatten_fields(filter_model)
    GeneratedFilter = create_model(  # ruff:ignore[non-lowercase-variable-in-function]
        f"Generated{filter_model.__name__}",
        **fields,
    )

    class FilterWrapper(GeneratedFilter):  # type: ignore[misc,valid-type]
        def __new__(cls, *args, **kwargs):
            try:
                instance = GeneratedFilter(*args, **kwargs)
                data = instance.model_dump(
                    exclude_unset=True, exclude_defaults=True, by_alias=by_alias
                )
                return _unflatten(filter_model, data)
            except ValidationError as e:
                raise RequestValidationError(e.errors()) from e

    return Depends(FilterWrapper)
