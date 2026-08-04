from collections.abc import Callable
from copy import deepcopy
from typing import Any, get_args, get_origin

from fastapi import Depends, Query, params
from fastapi.exceptions import RequestValidationError
from fastapi_filter.base.filter import BaseFilterModel
from pydantic import ValidationError, create_model

_ORDER_BY_FIELD_NAME = "order_by"


def _order_by_schema_extra(fields: list[str]) -> Callable[[dict[str, Any]], None]:
    """Return a json_schema_extra callable that injects all valid order_by values as enum.

    Each field is expanded to unprefixed (ascending), `+` (ascending), and `-` (descending).
    """
    enum = [f"{prefix}{f}" for prefix in ("", "+", "-") for f in fields]

    def extra(s: dict) -> None:
        s.update({"items": {"type": "string", "enum": enum}})

    return extra


def _prepare_filter_fields(filter_model: type[BaseFilterModel]) -> dict[str, Any]:
    """Convert list fields to Query params and inject the order_by enum for OpenAPI.

    Returns a field definitions dict suitable for passing to `create_model`.
    """
    fields = {}
    ordering_fields: list[str] | None = getattr(
        getattr(filter_model, "Constants", None), "ordering_model_fields", None
    )
    for name, f in filter_model.model_fields.items():
        field_info = deepcopy(f)
        annotation = f.annotation

        if (
            annotation is list
            or get_origin(annotation) is list
            or any(get_origin(a) is list for a in get_args(annotation))
        ) and type(field_info.default) is not params.Query:
            field_info.default = Query(default=field_info.default)
            if name == _ORDER_BY_FIELD_NAME and ordering_fields:
                # FastAPI's Query restricts json_schema_extra to dict | None, but Pydantic's
                # underlying FieldInfo supports callables, so we assign after construction.
                field_info.default.json_schema_extra = _order_by_schema_extra(ordering_fields)  # type: ignore[method-assign]

        fields[name] = (f.annotation, field_info)

    return fields


def FilterDepends(filter_model: type[BaseFilterModel], *, by_alias: bool = False, **_) -> Any:
    """Return a FastAPI dependency that parses query parameters into a filter model instance.

    FastAPI treats `list` fields as request body unless their default is a `Query` object.
    This builds a `GeneratedFilter` with list fields wrapped in `Query`, used by FastAPI for
    OpenAPI schema generation and query param parsing. The actual validation and construction
    of `filter_model` happens inside `FilterWrapper.__new__`.
    """
    fields = _prepare_filter_fields(filter_model)
    GeneratedFilter = create_model(filter_model.__class__.__name__, **fields)  # ruff:ignore[non-lowercase-variable-in-function]

    class FilterWrapper(GeneratedFilter):  # type: ignore[misc,valid-type]
        def __new__(cls, *args, **kwargs):
            try:
                instance = GeneratedFilter(*args, **kwargs)
                data = instance.model_dump(
                    exclude_unset=True, exclude_defaults=True, by_alias=by_alias
                )
                if original_filter := getattr(filter_model.Constants, "original_filter", None):
                    prefix = f"{filter_model.Constants.prefix}__"
                    stripped = {k.removeprefix(prefix): v for k, v in data.items()}
                    return original_filter(**stripped)
                return filter_model(**data)
            except ValidationError as e:
                raise RequestValidationError(e.errors()) from e

    return Depends(FilterWrapper)
