import json
from unittest.mock import patch

import pytest

from repo_name_checker.cli import main
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
        m.assert_called_once_with("foo", registries=None)
        out = capsys.readouterr().out
        assert "npm" in out
        assert "pypi" in out

    def it_passes_repeatable_registry_flag_through_to_sdk(fake_results):
        with patch("repo_name_checker.cli.check_sync", return_value=fake_results) as m:
            main(["foo", "--registry", "npm", "--registry", "pypi"])
        m.assert_called_once_with("foo", registries=["npm", "pypi"])

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
            {"registry": "npm", "name": "foo", "available": False},
            {"registry": "pypi", "name": "foo", "available": True},
        ]

    def it_rejects_unknown_format(capsys):
        with pytest.raises(SystemExit):
            main(["foo", "--format", "yaml"])
