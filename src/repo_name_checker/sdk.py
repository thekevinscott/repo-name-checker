import asyncio
from collections.abc import Iterable

import httpx

from repo_name_checker.registries import REGISTRIES, Registry, RegistryError
from repo_name_checker.types import CheckResult

DEFAULT_TIMEOUT = 10.0
DEFAULT_CONNECT_TIMEOUT = 5.0


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


def _format_error(exc: BaseException) -> str:
    message = str(exc).strip()
    cls = type(exc).__name__
    return f"{cls}: {message}" if message else cls


async def _run_one(
    registry: Registry, client: httpx.AsyncClient, name: str
) -> CheckResult:
    try:
        report = await registry.check(client, name)
    except (httpx.HTTPError, RegistryError) as exc:
        return CheckResult(
            registry=registry.name,
            name=name,
            available=False,
            error=_format_error(exc),
        )
    return CheckResult(
        registry=registry.name,
        name=name,
        available=report.available,
        collisions=report.collisions,
    )


async def check(
    name: str,
    *,
    registries: Iterable[str] | None = None,
    client: httpx.AsyncClient | None = None,
    timeout: float | httpx.Timeout | None = DEFAULT_TIMEOUT,
) -> list[CheckResult]:
    """Check `name` across the given registries (or all of them).

    Per-registry failures are returned as `CheckResult.error` rather than
    raised; one slow or broken registry never kills the run.
    """
    selected = _resolve(registries)
    owns_client = client is None
    if owns_client:
        if isinstance(timeout, httpx.Timeout) or timeout is None:
            effective_timeout = timeout
        else:
            effective_timeout = httpx.Timeout(
                timeout, connect=min(DEFAULT_CONNECT_TIMEOUT, timeout)
            )
        client = httpx.AsyncClient(
            timeout=effective_timeout, follow_redirects=True
        )
    assert client is not None
    try:
        results = await asyncio.gather(
            *(_run_one(registry, client, name) for registry in selected)
        )
    finally:
        if owns_client:
            await client.aclose()
    return list(results)


def check_sync(
    name: str,
    *,
    registries: Iterable[str] | None = None,
    timeout: float | httpx.Timeout | None = DEFAULT_TIMEOUT,
) -> list[CheckResult]:
    """Synchronous facade over `check` for callers outside an event loop."""
    return asyncio.run(check(name, registries=registries, timeout=timeout))


__all__ = [
    "DEFAULT_TIMEOUT",
    "REGISTRIES",
    "RegistryError",
    "UnknownRegistryError",
    "check",
    "check_sync",
]
