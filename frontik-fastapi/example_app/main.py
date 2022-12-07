import multiprocessing

from fastapi import FastAPI
from frontik.app import FrontikApplication
from frontik.loggers import bootstrap_core_logging
from frontik.options import options
from frontik.server import _run_worker

import routes
from example_app.pages.classic_handler import TestHandler
from ffapi.router import import_app_routes, frontik_handlers

fastapi_app = FastAPI(
    on_startup=[],
    on_shutdown=[],
    exception_handlers={},
    middleware=[],
)

import_app_routes(fastapi_app, routes, "app_router")


class TestFrontikApplication(FrontikApplication):
    def __init__(self, **settings):
        self.fastapi = fastapi_app
        super().__init__(**settings)

    def application_urls(self):
        return frontik_handlers(self.fastapi) + [('/classic_handler', TestHandler)]


def run_frontik_app(app_class, port):
    options.consul_enabled = False
    options.port = port
    options.debug = True
    options.autoreload = True
    options.app = "testapp"
    options.stderr_log = True
    bootstrap_core_logging()
    app = app_class(consul_enabled=False)
    _run_worker(app, multiprocessing.Lock(), True, None)


if __name__ == "__main__":
    run_frontik_app(TestFrontikApplication, 8080)
