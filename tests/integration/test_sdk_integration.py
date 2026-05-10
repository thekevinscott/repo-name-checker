"""Integration tests: exercise the SDK end-to-end with httpx mocked at the wire."""

import httpx
import pytest
import respx

from repo_name_checker import check, check_sync


@pytest.fixture
def all_taken():
    with respx.mock() as mock:
        mock.get("https://registry.npmjs.org/django").respond(200)
        mock.get("https://pypi.org/pypi/django/json").respond(200)
        mock.get("https://crates.io/api/v1/crates/django").respond(200)
        yield mock


@pytest.fixture
def all_available():
    with respx.mock() as mock:
        mock.get("https://registry.npmjs.org/zzznotreal").respond(404)
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

    async def it_propagates_network_errors():
        with respx.mock() as mock:
            mock.get("https://registry.npmjs.org/foo").mock(
                side_effect=httpx.ConnectError("boom")
            )
            with pytest.raises(httpx.ConnectError):
                await check("foo", registries=["npm"])
