import typing
from typing import Type

from pydantic import BaseModel

T = typing.TypeVar("T", bound=BaseModel)


def pydantic_deserializer(model: Type[T]) -> typing.Callable[[typing.Union[str, bytes]], T]:
    return lambda value: model.parse_raw(value)
