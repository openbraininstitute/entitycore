from collections.abc import Callable

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase

type ApplyOperations[T: DeclarativeBase] = Callable[[sa.Select[tuple[T]]], sa.Select[tuple[T]]]
