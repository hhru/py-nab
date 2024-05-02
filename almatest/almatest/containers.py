import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

from testcontainers.core.config import testcontainers_config
from testcontainers.core.container import DockerContainer

C = TypeVar("C", bound=DockerContainer)

# ryuk невозможно поднимать в тредах, потому что код Reaper-а в testcontainers нетредсейфный
testcontainers_config.ryuk_disabled = True


async def start_container(container: C) -> C:
    def _start_container():
        container.start()
        return container

    with ThreadPoolExecutor() as pool:
        return await asyncio.get_running_loop().run_in_executor(pool, _start_container)
