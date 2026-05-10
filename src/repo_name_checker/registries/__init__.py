from repo_name_checker.registries.base import HttpStatusRegistry, Registry, RegistryError
from repo_name_checker.registries.crates import CRATES
from repo_name_checker.registries.npm import NPM
from repo_name_checker.registries.pypi import PYPI

REGISTRIES: dict[str, Registry] = {NPM.name: NPM, PYPI.name: PYPI, CRATES.name: CRATES}

__all__ = [
    "CRATES",
    "HttpStatusRegistry",
    "NPM",
    "PYPI",
    "REGISTRIES",
    "Registry",
    "RegistryError",
]
