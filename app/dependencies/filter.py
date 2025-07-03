from copy import deepcopy
from typing import Any, get_args, get_origin

from fastapi import Depends, Query, params
from fastapi.exceptions import RequestValidationError
from fastapi_filter.base.filter import BaseFilterModel
from pydantic import ValidationError, create_model


def _list_to_query_fields(filter_model: type[BaseFilterModel]):
    fields = {}
    for name, f in filter_model.model_fields.items():
        field_info = deepcopy(f)
        annotation = f.annotation

        if (
            annotation is list
            or get_origin(annotation) is list
            or any(get_origin(a) is list for a in get_args(annotation))
        ) and type(field_info.default) is not params.Query:
            field_info.default = Query(default=field_info.default)

        fields[name] = (f.annotation, field_info)

    return fields


def FilterDepends(filter_model: type[BaseFilterModel], *, by_alias: bool = False, **_) -> Any:
    """Use a hack to treat lists as query parameters.

    What we do is loop through the fields of a filter and assign any `list` field a default value of
    `Query` so that FastAPI knows it should be treated a query parameter and not body.

    When we apply the filter, we build the original filter to properly validate the data (i.e. can
    the string be parsed and formatted as a list of <type>?)
    """
    fields = _list_to_query_fields(filter_model)
    GeneratedFilter = create_model(filter_model.__class__.__name__, **fields)  # noqa: N806

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
