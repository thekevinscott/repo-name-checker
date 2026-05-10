from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CheckResult:
    registry: str
    name: str
    available: bool
