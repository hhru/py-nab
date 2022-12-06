import asyncio
import dataclasses
import typing
from functools import wraps
from typing import Mapping, Callable, Any

from fastapi import params
from fastapi.dependencies.utils import solve_dependencies, get_dependant
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from ffapi.handler import current_scope


def sync_dep(func) -> params.Depends:
    return params.Depends(func)


T = typing.TypeVar("T")
V = typing.TypeVar("V")

_cache = {}


def async_dep(func: Callable[..., T]) -> T:
    if func in _cache:
        return params.Depends(_cache[func])

    @wraps(func)
    async def wrapper(*args, **kwargs):
        task = asyncio.create_task(func(*args, **kwargs))
        await asyncio.sleep(0)
        return task

    _cache[func] = wrapper
    return params.Depends(wrapper)


def await_dep(dep: typing.Coroutine[Any, Any, T]) -> T:
    async def wrapper(d: typing.Awaitable = dep):
        return await d

    return params.Depends(wrapper)


def wrap_by_lambda(value):
    return lambda: value


@dataclasses.dataclass
class DepsOverridesProvider:
    dependency_overrides: typing.Dict[Callable[..., Any], Any] = dataclasses.field(default_factory=dict)


DepsOverridesProvider.default_overrides = {}


class DepBuilder(typing.Generic[T]):
    def __init__(self, dep: Callable[..., T]) -> None:
        self.dep = dep
        self._path = ""
        self._scope: typing.Optional[Mapping] = current_scope.get(None)
        self._overrides: typing.Dict[Callable[..., V], Callable[..., V]] = {}

    def override(self, sub_dep: Callable[..., V], value: V) -> "DepBuilder[T]":
        self._overrides[sub_dep] = wrap_by_lambda(value)
        return self

    def path(self, path: str) -> "DepBuilder[T]":
        self._path = path
        return self

    def scope(self, scope: Mapping) -> "DepBuilder[T]":
        self._scope = scope
        return self

    async def build(self, request: Request = None) -> T:
        dependant = get_dependant(path=self._path, call=self.dep)

        all_overrides = {**DepsOverridesProvider.default_overrides, **self._overrides}
        overrides_provider = DepsOverridesProvider(dependency_overrides=all_overrides)
        if request is None:
            if self._scope is None:
                self._scope = {"type": "http", "query_string": "", "headers": []}
            request = Request(scope=self._scope)
            form = None
        else:
            form = await request.form()

        solved = await solve_dependencies(
            request=request,
            body=form,
            dependant=dependant,
            dependency_overrides_provider=overrides_provider,
        )

        values, errors, background_tasks, sub_response, dependency_cache = solved
        if errors:
            raise RequestValidationError(errors, body=form)

        return self.dep(**values)


async def build_dep(func: Callable[..., T], request: Request = None) -> T:
    return await DepBuilder(func).build(request)
