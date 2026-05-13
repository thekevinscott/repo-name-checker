"""Integration tests: exercise the SDK end-to-end with httpx mocked at the wire."""

import httpx
import pytest
import respx

from repo_name_checker import check, check_sync
from repo_name_checker.registries.npm import generate_variants

NPM_SEARCH = "https://registry.npmjs.org/-/v1/search"


def _mock_npm(mock, name: str, *, status: int) -> None:
    for variant in generate_variants(name):
        mock.get(f"https://registry.npmjs.org/{variant}").respond(status)
    mock.get(url__startswith=NPM_SEARCH).respond(
        json={"objects": [], "total": 0, "time": "now"}
    )


@pytest.fixture
def all_taken():
    with respx.mock() as mock:
        _mock_npm(mock, "django", status=200)
        mock.get("https://pypi.org/pypi/django/json").respond(200)
        mock.get("https://crates.io/api/v1/crates/django").respond(200)
        yield mock


@pytest.fixture
def all_available():
    with respx.mock() as mock:
        _mock_npm(mock, "zzznotreal", status=404)
        mock.get("https://pypi.org/pypi/zzznotreal/json").respond(404)
        mock.get("https://crates.io/api/v1/crates/zzznotreal").respond(404)
        yield mock


def describe_sdk_integration():
    async def it_reports_all_registries_as_taken(all_taken):
        results = await check("django")
        assert all(not r.available for r in results)

    async def it_reports_all_registries_as_available(all_available):
        results = await check("zzznotreal")
        assert all(r.available for r in results)

    def it_works_through_the_sync_helper(all_available):
        results = check_sync("zzznotreal")
        assert all(r.available for r in results)

    async def it_captures_network_errors_in_the_result():
        with respx.mock() as mock:
            mock.get("https://registry.npmjs.org/foo").mock(
                side_effect=httpx.ConnectError("boom")
            )
            mock.get(url__startswith=NPM_SEARCH).respond(
                json={"objects": [], "total": 0, "time": "now"}
            )
            results = await check("foo", registries=["npm"])
        assert len(results) == 1
        assert results[0].available is False
        assert results[0].error is not None
        assert "ConnectError" in results[0].error
