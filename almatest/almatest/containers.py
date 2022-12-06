import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

from testcontainers.core.container import DockerContainer

C = TypeVar("C", bound=DockerContainer)


async def start_container(container: C) -> C:
    def _start_container():
        container.start()
        return container

    with ThreadPoolExecutor() as pool:
        return await asyncio.get_running_loop().run_in_executor(pool, _start_container)
