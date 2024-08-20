from __future__ import annotations
import typing
from typing import Type

from pydantic import BaseModel

T = typing.TypeVar("T", bound=BaseModel)


def pydantic_deserializer(model: type[T]) -> typing.Callable[str | bytes, T]:
    return lambda value: model.parse_raw(value)
