import pytest
from testcontainers.postgres import PostgresContainer

from almatest.containers import start_container


@pytest.fixture(scope="session")
async def pg_container() -> PostgresContainer:
    container = await start_container(PostgresContainer("postgres:11.5-alpine", remove=True))
    yield container
    container.stop()
