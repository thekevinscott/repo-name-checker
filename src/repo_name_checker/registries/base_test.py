import httpx
import pytest
import respx

from repo_name_checker.registries.base import HttpStatusRegistry, RegistryError


@pytest.fixture
def registry() -> HttpStatusRegistry:
    return HttpStatusRegistry(
        name="fake",
        url_template="https://example.test/api/{name}",
        headers={"X-Test": "1"},
    )


def describe_http_status_registry():
    @pytest.mark.parametrize(
        ("status_code", "expected"),
        [
            (404, True),
            (200, False),
        ],
    )
    async def it_maps_status_to_availability(
        registry: HttpStatusRegistry, status_code: int, expected: bool
    ) -> None:
        with respx.mock(assert_all_called=True) as mock:
            route = mock.get("https://example.test/api/foo").respond(status_code)
            async with httpx.AsyncClient() as client:
                assert await registry.is_available(client, "foo") is expected
            assert route.calls.last.request.headers["X-Test"] == "1"

    async def it_url_encodes_the_name(registry: HttpStatusRegistry) -> None:
        with respx.mock(assert_all_called=True) as mock:
            mock.get("https://example.test/api/%40scope%2Fpkg").respond(404)
            async with httpx.AsyncClient() as client:
                assert await registry.is_available(client, "@scope/pkg") is True

    async def it_raises_on_unexpected_status(registry: HttpStatusRegistry) -> None:
        with respx.mock() as mock:
            mock.get("https://example.test/api/foo").respond(500)
            async with httpx.AsyncClient() as client:
                with pytest.raises(RegistryError):
                    await registry.is_available(client, "foo")
