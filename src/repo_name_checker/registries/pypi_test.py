from repo_name_checker.registries.pypi import PYPI


def describe_pypi_registry():
    def it_uses_pypi_name():
        assert PYPI.name == "pypi"

    def it_targets_the_pypi_json_api():
        assert PYPI.url_template == "https://pypi.org/pypi/{name}/json"
