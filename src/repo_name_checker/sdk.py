import asyncio
from collections.abc import Iterable

import httpx

from repo_name_checker.registries import REGISTRIES, Registry, RegistryError
from repo_name_checker.types import CheckResult


class UnknownRegistryError(KeyError):
    """Raised when a caller asks for a registry the SDK doesn't know about."""


def _resolve(registries: Iterable[str] | None) -> list[Registry]:
    if registries is None:
        return list(REGISTRIES.values())
    selected: list[Registry] = []
    for name in registries:
        try:
            selected.append(REGISTRIES[name])
        except KeyError as exc:
            known = ", ".join(REGISTRIES)
            raise UnknownRegistryError(
                f"unknown registry {name!r}; known registries: {known}"
            ) from exc
    return selected


async def check(
    name: str,
    *,
    registries: Iterable[str] | None = None,
    client: httpx.AsyncClient | None = None,
) -> list[CheckResult]:
    """Check `name` across the given registries (or all of them)."""
    selected = _resolve(registries)
    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=10.0, follow_redirects=True)
    try:
        availabilities = await asyncio.gather(
            *(registry.is_available(client, name) for registry in selected)
        )
    finally:
        if owns_client:
            await client.aclose()
    return [
        CheckResult(registry=registry.name, name=name, available=available)
        for registry, available in zip(selected, availabilities, strict=True)
    ]


def check_sync(
    name: str, *, registries: Iterable[str] | None = None
) -> list[CheckResult]:
    """Synchronous facade over `check` for callers outside an event loop."""
    return asyncio.run(check(name, registries=registries))


__all__ = [
    "REGISTRIES",
    "RegistryError",
    "UnknownRegistryError",
    "check",
    "check_sync",
]
