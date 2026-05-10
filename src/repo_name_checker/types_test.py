from dataclasses import FrozenInstanceError

import pytest

from repo_name_checker.types import CheckResult


def describe_check_result():
    def it_holds_registry_name_and_availability():
        result = CheckResult(registry="npm", name="foo", available=True)
        assert result.registry == "npm"
        assert result.name == "foo"
        assert result.available is True

    def it_is_frozen():
        result = CheckResult(registry="npm", name="foo", available=True)
        with pytest.raises(FrozenInstanceError):
            result.available = False  # type: ignore[misc]
