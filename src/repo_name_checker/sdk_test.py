import pytest
import respx

from repo_name_checker.sdk import (
    REGISTRIES,
    UnknownRegistryError,
    check,
    check_sync,
)
from repo_name_checker.types import CheckResult


SEARCH_URL = "https://registry.npmjs.org/-/v1/search"


@pytest.fixture
def all_registries_mocked():
    with respx.mock(assert_all_called=False) as mock:
        for variant in ("foo",):
            mock.get(f"https://registry.npmjs.org/{variant}").respond(404)
        mock.get(url__startswith=SEARCH_URL).respond(
            json={"objects": [], "total": 0, "time": "now"}
        )
        mock.get("https://pypi.org/pypi/foo/json").respond(200)
        mock.get("https://crates.io/api/v1/crates/foo").respond(404)
        yield mock


def describe_check():
    async def it_returns_a_result_per_registry_in_order(all_registries_mocked):
        results = await check("foo")
        assert results == [
            CheckResult(registry="npm", name="foo", available=True),
            CheckResult(registry="pypi", name="foo", available=False),
            CheckResult(registry="crates", name="foo", available=True),
        ]

    async def it_filters_to_selected_registries(all_registries_mocked):
        results = await check("foo", registries=["pypi"])
        assert results == [CheckResult(registry="pypi", name="foo", available=False)]

    async def it_preserves_caller_specified_registry_order():
        with respx.mock() as mock:
            mock.get("https://crates.io/api/v1/crates/foo").respond(404)
            mock.get("https://registry.npmjs.org/foo").respond(200)
            mock.get(url__startswith=SEARCH_URL).respond(
                json={"objects": [], "total": 0, "time": "now"}
            )
            results = await check("foo", registries=["crates", "npm"])
        assert [r.registry for r in results] == ["crates", "npm"]

    async def it_rejects_unknown_registry_names():
        with pytest.raises(UnknownRegistryError):
            await check("foo", registries=["bogus"])

    async def it_passes_npm_collisions_through_to_check_result():
        with respx.mock() as mock:
            mock.get("https://registry.npmjs.org/darkfactory").respond(404)
            mock.get(url__startswith=SEARCH_URL).respond(
                json={
                    "objects": [{"package": {"name": "dark-factory"}}],
                    "total": 1,
                    "time": "now",
                }
            )
            results = await check("darkfactory", registries=["npm"])
        assert results[0].available is False
        assert "dark-factory" in results[0].collisions


def describe_check_sync():
    def it_runs_check_synchronously(all_registries_mocked):
        results = check_sync("foo", registries=["npm"])
        assert results == [CheckResult(registry="npm", name="foo", available=True)]


def describe_registries_mapping():
    def it_exposes_all_three_default_registries():
        assert set(REGISTRIES) == {"npm", "pypi", "crates"}
