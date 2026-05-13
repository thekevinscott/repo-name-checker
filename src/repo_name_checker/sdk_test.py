import httpx
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

    async def it_tolerates_one_registry_timing_out():
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://registry.npmjs.org/foo").mock(
                side_effect=httpx.ConnectTimeout("connect timed out")
            )
            mock.get(url__startswith=SEARCH_URL).respond(
                json={"objects": [], "total": 0, "time": "now"}
            )
            mock.get("https://pypi.org/pypi/foo/json").respond(404)
            results = await check("foo", registries=["npm", "pypi"])
        by_registry = {r.registry: r for r in results}
        assert by_registry["npm"].error is not None
        assert "ConnectTimeout" in by_registry["npm"].error
        assert by_registry["npm"].available is False
        assert by_registry["pypi"].available is True
        assert by_registry["pypi"].error is None

    async def it_tolerates_unexpected_status_codes_from_one_registry():
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://crates.io/api/v1/crates/foo").respond(503)
            mock.get("https://pypi.org/pypi/foo/json").respond(404)
            results = await check("foo", registries=["crates", "pypi"])
        by_registry = {r.registry: r for r in results}
        assert by_registry["crates"].error is not None
        assert "503" in by_registry["crates"].error
        assert by_registry["pypi"].available is True

    async def it_returns_results_in_caller_order_even_with_errors():
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://pypi.org/pypi/foo/json").mock(
                side_effect=httpx.ReadTimeout("read timed out")
            )
            mock.get("https://crates.io/api/v1/crates/foo").respond(404)
            results = await check("foo", registries=["pypi", "crates"])
        assert [r.registry for r in results] == ["pypi", "crates"]
        assert results[0].error is not None
        assert results[1].available is True


def describe_check_sync():
    def it_runs_check_synchronously(all_registries_mocked):
        results = check_sync("foo", registries=["npm"])
        assert results == [CheckResult(registry="npm", name="foo", available=True)]


def describe_registries_mapping():
    def it_exposes_all_three_default_registries():
        assert set(REGISTRIES) == {"npm", "pypi", "crates"}
