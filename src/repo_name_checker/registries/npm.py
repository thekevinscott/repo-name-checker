"""npm registry checker with publish-time collision detection.

npm's registry rejects publishes whose normalized form (lowercased, with
``-``/``_``/``.`` removed) matches an existing package. ``check`` enumerates
every separator-swap variant of the candidate, GETs each, and additionally
queries npm's search endpoint to catch insertion-style collisions where the
candidate has no separators (e.g. ``darkfactory`` vs ``dark-factory``).

The check is best-effort: npm's exact internal algorithm is private and may
drift, so a passing check is necessary but not sufficient.
"""

import asyncio
import itertools
from urllib.parse import quote

import httpx

from repo_name_checker.registries.base import RegistryError
from repo_name_checker.types import RegistryReport

_SEPARATORS = ("-", "_", ".", "")
_SEPARATOR_CHARS = set("-_.")
_REGISTRY = "https://registry.npmjs.org"
_SEARCH = f"{_REGISTRY}/-/v1/search"
_SEARCH_SIZE = 50
# Cap on separators we fan out across; above this we fall back to lowered + collapsed
# to avoid 4**N variant explosion. Search still catches insertion-style collisions.
_MAX_SEPARATORS_FOR_VARIANTS = 3


def normalize(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch not in _SEPARATOR_CHARS)


def generate_variants(name: str) -> list[str]:
    """Every separator-swap variant of ``name`` (including the collapsed form)."""
    lowered = name.lower()
    parts: list[str] = []
    current: list[str] = []
    for ch in lowered:
        if ch in _SEPARATOR_CHARS:
            if current:
                parts.append("".join(current))
                current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))

    if len(parts) <= 1:
        return [lowered]

    sep_count = len(parts) - 1
    if sep_count > _MAX_SEPARATORS_FOR_VARIANTS:
        return list(dict.fromkeys([lowered, "".join(parts)]))

    variants: list[str] = []
    for combo in itertools.product(_SEPARATORS, repeat=sep_count):
        out = parts[0]
        for sep, part in zip(combo, parts[1:], strict=True):
            out += sep + part
        variants.append(out)
    return variants


async def _exists(client: httpx.AsyncClient, name: str) -> bool:
    response = await client.get(f"{_REGISTRY}/{quote(name, safe='')}")
    match response.status_code:
        case 200:
            return True
        case 404:
            return False
        case code:
            raise RegistryError(f"npm: unexpected status {code} for {name!r}")


async def _search_collisions(
    client: httpx.AsyncClient, candidate: str
) -> list[str]:
    target = normalize(candidate)
    response = await client.get(_SEARCH, params={"text": target, "size": _SEARCH_SIZE})
    response.raise_for_status()
    payload = response.json()
    hits: list[str] = []
    for entry in payload.get("objects", []):
        hit_name = entry.get("package", {}).get("name", "")
        if hit_name and hit_name != candidate and normalize(hit_name) == target:
            hits.append(hit_name)
    return hits


class NpmRegistry:
    name = "npm"

    async def check(
        self, client: httpx.AsyncClient, package_name: str
    ) -> RegistryReport:
        variants = generate_variants(package_name)
        existence, search_hits = await asyncio.gather(
            asyncio.gather(*(_exists(client, v) for v in variants)),
            _search_collisions(client, package_name),
        )
        direct_hits = [
            v for v, exists in zip(variants, existence, strict=True)
            if exists and v != package_name.lower()
        ]
        collisions = list(dict.fromkeys(direct_hits + search_hits))
        exact_taken = any(
            exists and v == package_name.lower()
            for v, exists in zip(variants, existence, strict=True)
        )
        available = not (collisions or exact_taken)
        return RegistryReport(available=available, collisions=tuple(collisions))


NPM = NpmRegistry()
