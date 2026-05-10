import httpx
import pytest
import respx

from repo_name_checker.registries.npm import NPM, generate_variants, normalize


def describe_normalize():
    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("dark-factory", "darkfactory"),
            ("dark_factory", "darkfactory"),
            ("dark.factory", "darkfactory"),
            ("Dark-Factory", "darkfactory"),
            ("darkfactory", "darkfactory"),
            ("a-b-c", "abc"),
            ("foo.bar_baz-qux", "foobarbazqux"),
        ],
    )
    def it_collapses_punctuation_and_lowercases(name, expected):
        assert normalize(name) == expected


def describe_generate_variants():
    def it_returns_just_the_lowercased_name_when_no_separators():
        assert generate_variants("darkfactory") == ["darkfactory"]

    def it_enumerates_every_separator_combination():
        variants = generate_variants("dark-factory")
        assert set(variants) == {"dark-factory", "dark_factory", "dark.factory", "darkfactory"}

    def it_enumerates_combinations_for_multiple_separators():
        variants = generate_variants("a-b.c")
        # 4 separators * 4 separators = 16 combos
        assert len(set(variants)) == 16
        assert "a-b-c" in variants
        assert "abc" in variants
        assert "a.b_c" in variants

    def it_lowercases_input():
        assert "dark-factory" in generate_variants("Dark-Factory")

    def it_caps_variant_explosion_for_many_separators():
        # 7 separators would be 4**7 = 16384 GETs; that's runaway.
        variants = generate_variants("a-b-c-d-e-f-g-h")
        assert len(variants) <= 64
        assert "a-b-c-d-e-f-g-h" in variants
        assert "abcdefgh" in variants


def describe_npm_registry_metadata():
    def it_uses_npm_name():
        assert NPM.name == "npm"


SEARCH_URL = "https://registry.npmjs.org/-/v1/search"


def _mock_search_empty(mock):
    mock.get(url__startswith=SEARCH_URL).respond(
        json={"objects": [], "total": 0, "time": "now"}
    )


def describe_npm_check():
    async def it_reports_available_when_no_variant_exists() -> None:
        with respx.mock(assert_all_called=False) as mock:
            for variant in ("dark-factory", "dark_factory", "dark.factory", "darkfactory"):
                mock.get(f"https://registry.npmjs.org/{variant}").respond(404)
            _mock_search_empty(mock)
            async with httpx.AsyncClient() as client:
                report = await NPM.check(client, "dark-factory")
        assert report.available is True
        assert report.collisions == ()

    async def it_flags_separator_swap_collisions() -> None:
        # Candidate has separators; we GET every variant directly.
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://registry.npmjs.org/dark-factory").respond(404)
            mock.get("https://registry.npmjs.org/dark_factory").respond(200)
            mock.get("https://registry.npmjs.org/dark.factory").respond(404)
            mock.get("https://registry.npmjs.org/darkfactory").respond(404)
            _mock_search_empty(mock)
            async with httpx.AsyncClient() as client:
                report = await NPM.check(client, "dark-factory")
        assert report.available is False
        assert "dark_factory" in report.collisions

    async def it_uses_search_to_catch_insertion_style_collisions() -> None:
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://registry.npmjs.org/darkfactory").respond(404)
            mock.get(url__startswith=SEARCH_URL).respond(
                json={
                    "objects": [
                        {"package": {"name": "dark-factory"}},
                        {"package": {"name": "darkroom"}},
                    ],
                    "total": 2,
                    "time": "now",
                }
            )
            async with httpx.AsyncClient() as client:
                report = await NPM.check(client, "darkfactory")
        assert report.available is False
        assert "dark-factory" in report.collisions
        assert "darkroom" not in report.collisions

    async def it_does_not_list_the_candidate_itself_as_a_collision() -> None:
        with respx.mock(assert_all_called=False) as mock:
            mock.get("https://registry.npmjs.org/foo").respond(200)
            _mock_search_empty(mock)
            async with httpx.AsyncClient() as client:
                report = await NPM.check(client, "foo")
        assert report.available is False
        # Candidate itself isn't a "collision" — it's the exact-match taken case.
        assert "foo" not in report.collisions
