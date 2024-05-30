import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

from testcontainers.core.config import testcontainers_config
from testcontainers.core.container import DockerContainer
from testcontainers.core.utils import inside_container

C = TypeVar("C", bound=DockerContainer)

# ryuk невозможно поднимать в тредах, потому что код Reaper-а в testcontainers нетредсейфный
testcontainers_config.ryuk_disabled = True


async def start_container(container: C) -> C:
    def _start_container():
        container.start()
        return container

    with ThreadPoolExecutor() as pool:
        return await asyncio.get_running_loop().run_in_executor(pool, _start_container)


class HHContainer(DockerContainer):
    """
    Реверт изменений из коммита
    https://github.com/testcontainers/testcontainers-python/commit/2db8e6d123d42b57309408dd98ba9a06acc05c4b
    в котором сломали определение адреса хоста когда тесты и тестконтейнеры запускаются в докер-контейнере
    """

    def get_container_host_ip(self) -> str:
        host = self.get_docker_client().host()
        if not host:
            return "localhost"

        # check testcontainers itself runs inside docker container
        if inside_container() and not os.getenv("DOCKER_HOST") and not host.startswith("http://"):
            # If newly spawned container's gateway IP address from the docker
            # "bridge" network is equal to detected host address, we should use
            # container IP address, otherwise fall back to detected host
            # address. Even it's inside container, we need to double check,
            # because docker host might be set to docker:dind, usually in CI/CD environment
            gateway_ip = self.get_docker_client().gateway_ip(self._container.id)

            if gateway_ip == host:
                return self.get_docker_client().bridge_ip(self._container.id)
            return gateway_ip
        return host
