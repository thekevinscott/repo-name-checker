from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import quote

import httpx

from repo_name_checker.types import RegistryReport


class RegistryError(RuntimeError):
    """Raised when a registry returns an unexpected response."""


class Registry(Protocol):
    name: str

    async def check(self, client: httpx.AsyncClient, package_name: str) -> RegistryReport: ...


@dataclass(frozen=True, slots=True)
class HttpStatusRegistry:
    name: str
    url_template: str
    headers: Mapping[str, str] = field(default_factory=dict)

    async def check(
        self, client: httpx.AsyncClient, package_name: str
    ) -> RegistryReport:
        url = self.url_template.format(name=quote(package_name, safe=""))
        response = await client.get(url, headers=dict(self.headers))
        match response.status_code:
            case 404:
                return RegistryReport(available=True)
            case 200:
                return RegistryReport(available=False)
            case code:
                raise RegistryError(
                    f"{self.name}: unexpected status {code} for {package_name!r}"
                )
