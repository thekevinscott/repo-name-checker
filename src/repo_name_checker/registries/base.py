from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import quote

import httpx


class RegistryError(RuntimeError):
    """Raised when a registry returns an unexpected response."""


class Registry(Protocol):
    name: str

    async def is_available(self, client: httpx.AsyncClient, package_name: str) -> bool: ...


@dataclass(frozen=True, slots=True)
class HttpStatusRegistry:
    name: str
    url_template: str
    headers: Mapping[str, str] = field(default_factory=dict)

    async def is_available(self, client: httpx.AsyncClient, package_name: str) -> bool:
        url = self.url_template.format(name=quote(package_name, safe=""))
        response = await client.get(url, headers=dict(self.headers))
        match response.status_code:
            case 404:
                return True
            case 200:
                return False
            case code:
                raise RegistryError(
                    f"{self.name}: unexpected status {code} for {package_name!r}"
                )
