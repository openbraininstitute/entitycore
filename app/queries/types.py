from collections.abc import Callable
from typing import Any, Protocol

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

type ApplyOperations[T: DeclarativeBase] = Callable[[sa.Select[tuple[T]]], sa.Select[tuple[T]]]


class SupportsModelValidate[T: BaseModel](Protocol):
    @classmethod
    def model_validate(cls, obj: Any, *args, **kwargs) -> T: ...
