import asyncio
import importlib
import pkgutil
from functools import wraps
from typing import Callable, Any, Tuple

from fastapi import FastAPI
from fastapi.routing import APIRoute
from frontik.handler import PageHandler

from ffapi.handler import frontik_asgi_handler


class FrontikFastAPIRoute(APIRoute):
    def __init__(self, path: str, endpoint: Callable[..., Any], **kwargs):
        @wraps(endpoint)
        async def endpoint_wrapper(*args, **kwargs):
            await asyncio.sleep(0)
            return await endpoint(*args, **kwargs)

        super().__init__(path, endpoint=endpoint_wrapper, **kwargs)


def frontik_handlers(fastapi_app: FastAPI):
    return [frontik_handler(fastapi_app, router) for router in fastapi_app.routes]


def frontik_handler(fastapi_app: FastAPI, router: FrontikFastAPIRoute) -> Tuple[str, PageHandler]:
    return (
        router.path_regex.pattern.replace("$", ".*"),
        frontik_asgi_handler(fastapi_app),
    )


def import_app_routes(application: FastAPI, search_module, search_field: str = "app_router"):
    _try_add_router(application, search_field, search_module)
    for _, module, __ in pkgutil.walk_packages(search_module.__path__, prefix=f"{search_module.__package__}."):
        imported_module = importlib.import_module(module)
        _try_add_router(application, search_field, imported_module)


def _try_add_router(application, search_field, search_module):
    router = getattr(search_module, search_field, None)
    if router is not None:
        application.include_router(router)
