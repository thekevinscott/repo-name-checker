from repo_name_checker.registries.base import HttpStatusRegistry

PYPI = HttpStatusRegistry(name="pypi", url_template="https://pypi.org/pypi/{name}/json")
