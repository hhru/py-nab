from typing import Callable

from sqlalchemy.engine import url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from ararat.serialize.common import json_serialize as json_serializer_obj


def get_engine_urls(raw_url):
    parsed_url: url.URL = url.make_url(raw_url)
    if parsed_url.host:
        yield raw_url
        return

    if not parsed_url.normalized_query.get("host"):
        raise Exception("Cannot connect to database - no host specified")

    clean_query = {k: v for k, v in parsed_url.normalized_query.items() if k != "host"}
    for host_port in parsed_url.normalized_query.get("host"):
        host, _, port = host_port.partition(":")
        host_url = parsed_url._replace(host=host, port=int(port), query=clean_query).render_as_string(
            hide_password=False
        )
        yield host_url


def get_engine(
    raw_url, echo=False, future=True, json_serializer: Callable[[dict], str] = json_serializer_obj, **kwargs
) -> AsyncEngine:
    for engine_url in get_engine_urls(raw_url):
        try:
            engine: AsyncEngine = create_async_engine(
                engine_url, echo=echo, future=future, json_serializer=json_serializer, **kwargs
            )
            engine.connect()
            return engine
        except Exception as e:
            exc = e
    raise exc
