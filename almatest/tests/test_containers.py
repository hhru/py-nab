import asyncio

from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from almatest.containers import start_container


async def test_run_containers():
    containers = await asyncio.gather(
        start_container(PostgresContainer("postgres:14.7-alpine", remove=True)),
        start_container(RedisContainer("redis:7.0.3", remove=True)),
    )
    for c in containers:
        c.stop()
