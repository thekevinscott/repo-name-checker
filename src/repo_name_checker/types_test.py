from dataclasses import FrozenInstanceError

import pytest

from repo_name_checker.types import CheckResult, RegistryReport


def describe_check_result():
    def it_holds_registry_name_and_availability():
        result = CheckResult(registry="npm", name="foo", available=True)
        assert result.registry == "npm"
        assert result.name == "foo"
        assert result.available is True
        assert result.collisions == ()

    def it_carries_optional_collisions():
        result = CheckResult(
            registry="npm", name="darkfactory", available=False, collisions=("dark-factory",)
        )
        assert result.collisions == ("dark-factory",)

    def it_is_frozen():
        result = CheckResult(registry="npm", name="foo", available=True)
        with pytest.raises(FrozenInstanceError):
            result.available = False  # type: ignore[misc]


def describe_registry_report():
    def it_defaults_collisions_to_empty():
        report = RegistryReport(available=True)
        assert report.collisions == ()

    def it_is_frozen():
        report = RegistryReport(available=True)
        with pytest.raises(FrozenInstanceError):
            report.available = False  # type: ignore[misc]
