from repo_name_checker.registries.crates import CRATES


def describe_crates_registry():
    def it_uses_crates_name():
        assert CRATES.name == "crates"

    def it_targets_the_crates_api():
        assert CRATES.url_template == "https://crates.io/api/v1/crates/{name}"

    def it_sends_a_user_agent_because_crates_requires_one():
        assert "User-Agent" in CRATES.headers
        assert CRATES.headers["User-Agent"]
