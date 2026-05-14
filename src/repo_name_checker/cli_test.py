import json
from unittest.mock import patch

import pytest

from repo_name_checker.cli import main
from repo_name_checker.sdk import DEFAULT_TIMEOUT
from repo_name_checker.types import CheckResult


@pytest.fixture
def fake_results():
    return [
        CheckResult(registry="npm", name="foo", available=False),
        CheckResult(registry="pypi", name="foo", available=True),
    ]


def describe_cli():
    def it_invokes_the_sdk_with_positional_name(fake_results, capsys):
        with patch("repo_name_checker.cli.check_sync", return_value=fake_results) as m:
            exit_code = main(["foo"])
        assert exit_code == 0
        m.assert_called_once_with("foo", registries=None, timeout=DEFAULT_TIMEOUT)
        out = capsys.readouterr().out
        assert "npm" in out
        assert "pypi" in out

    def it_passes_repeatable_registry_flag_through_to_sdk(fake_results):
        with patch("repo_name_checker.cli.check_sync", return_value=fake_results) as m:
            main(["foo", "--registry", "npm", "--registry", "pypi"])
        m.assert_called_once_with(
            "foo", registries=["npm", "pypi"], timeout=DEFAULT_TIMEOUT
        )

    def it_forwards_timeout_flag_to_sdk(fake_results):
        with patch("repo_name_checker.cli.check_sync", return_value=fake_results) as m:
            main(["foo", "--timeout", "2.5"])
        m.assert_called_once_with("foo", registries=None, timeout=2.5)

    def it_returns_nonzero_when_no_registries_have_availability(capsys):
        all_taken = [
            CheckResult(registry="npm", name="foo", available=False),
            CheckResult(registry="pypi", name="foo", available=False),
        ]
        with patch("repo_name_checker.cli.check_sync", return_value=all_taken):
            exit_code = main(["foo"])
        assert exit_code == 1

    @pytest.mark.parametrize(
        ("argv", "format_marker"),
        [
            (["foo"], "Available"),
            (["foo", "--format", "table"], "Available"),
        ],
    )
    def it_renders_a_table_by_default(fake_results, capsys, argv, format_marker):
        with patch("repo_name_checker.cli.check_sync", return_value=fake_results):
            main(argv)
        out = capsys.readouterr().out
        assert format_marker in out

    def it_emits_json_when_requested(fake_results, capsys):
        with patch("repo_name_checker.cli.check_sync", return_value=fake_results):
            main(["foo", "--format", "json"])
        payload = json.loads(capsys.readouterr().out)
        assert payload == [
            {
                "registry": "npm",
                "name": "foo",
                "available": False,
                "collisions": [],
                "error": None,
            },
            {
                "registry": "pypi",
                "name": "foo",
                "available": True,
                "collisions": [],
                "error": None,
            },
        ]

    def it_rejects_unknown_format(capsys):
        with pytest.raises(SystemExit):
            main(["foo", "--format", "yaml"])

    def it_includes_collisions_in_table_output(capsys):
        results = [
            CheckResult(
                registry="npm",
                name="darkfactory",
                available=False,
                collisions=("dark-factory", "dark_factory"),
            ),
        ]
        with patch("repo_name_checker.cli.check_sync", return_value=results):
            main(["darkfactory"])
        out = capsys.readouterr().out
        assert "dark-factory" in out
        assert "dark_factory" in out

    def it_includes_collisions_in_json_output(capsys):
        results = [
            CheckResult(
                registry="npm",
                name="darkfactory",
                available=False,
                collisions=("dark-factory",),
            ),
        ]
        with patch("repo_name_checker.cli.check_sync", return_value=results):
            main(["darkfactory", "--format", "json"])
        payload = json.loads(capsys.readouterr().out)
        assert payload[0]["collisions"] == ["dark-factory"]

    def it_renders_errors_in_table_without_crashing(capsys):
        results = [
            CheckResult(
                registry="npm",
                name="foo",
                available=False,
                error="ConnectTimeout: dialing registry.npmjs.org",
            ),
            CheckResult(registry="pypi", name="foo", available=True),
        ]
        with patch("repo_name_checker.cli.check_sync", return_value=results):
            exit_code = main(["foo"])
        out = capsys.readouterr().out
        assert "ConnectTimeout" in out
        # pypi is still available → exit 0
        assert exit_code == 0

    def it_returns_nonzero_when_all_registries_error(capsys):
        results = [
            CheckResult(registry="npm", name="foo", available=False, error="boom"),
            CheckResult(registry="pypi", name="foo", available=False, error="boom"),
        ]
        with patch("repo_name_checker.cli.check_sync", return_value=results):
            exit_code = main(["foo"])
        assert exit_code == 1

    def it_includes_error_in_json_output(capsys):
        results = [
            CheckResult(
                registry="npm",
                name="foo",
                available=False,
                error="ConnectTimeout",
            ),
        ]
        with patch("repo_name_checker.cli.check_sync", return_value=results):
            main(["foo", "--format", "json"])
        payload = json.loads(capsys.readouterr().out)
        assert payload[0]["error"] == "ConnectTimeout"

    @pytest.mark.parametrize("flag", ["--version", "-V"])
    def it_prints_version_and_exits_zero(capsys, flag):
        with pytest.raises(SystemExit) as exc:
            main([flag])
        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert out.startswith("repo-name-checker ")
        # version should look like a PEP 440 version, not the unknown placeholder
        version_str = out.split(" ", 1)[1].strip()
        assert version_str
        assert not version_str.startswith("0.0.0+unknown")
