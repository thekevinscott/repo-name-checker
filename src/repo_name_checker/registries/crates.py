from types import MappingProxyType

from repo_name_checker.registries.base import HttpStatusRegistry

CRATES = HttpStatusRegistry(
    name="crates",
    url_template="https://crates.io/api/v1/crates/{name}",
    headers=MappingProxyType(
        {"User-Agent": "repo-name-checker (https://github.com/thekevinscott/repo-name-checker)"}
    ),
)
