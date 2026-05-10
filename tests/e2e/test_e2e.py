"""End-to-end tests against real registries. Network required.

Run with: uv run pytest -m e2e
"""

import pytest

from repo_name_checker import check

pytestmark = pytest.mark.e2e


# A name that's astronomically unlikely to ever be claimed on any of these registries.
UNCLAIMED = "rnczzznevercannotexist9f3e2a"


def describe_e2e_real_registries():
    @pytest.mark.parametrize("registry", ["npm", "pypi", "crates"])
    async def it_reports_a_well_known_name_as_taken(registry: str) -> None:
        taken = {"npm": "react", "pypi": "django", "crates": "serde"}[registry]
        results = await check(taken, registries=[registry])
        assert results[0].available is False

    @pytest.mark.parametrize("registry", ["npm", "pypi", "crates"])
    async def it_reports_an_unclaimed_name_as_available(registry: str) -> None:
        results = await check(UNCLAIMED, registries=[registry])
        assert results[0].available is True
