from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CheckResult:
    registry: str
    name: str
    available: bool
    collisions: tuple[str, ...] = ()
    error: str | None = None


@dataclass(frozen=True, slots=True)
class RegistryReport:
    available: bool
    collisions: tuple[str, ...] = field(default=())
