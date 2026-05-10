from repo_name_checker.registries.npm import NPM


def describe_npm_registry():
    def it_uses_npm_name():
        assert NPM.name == "npm"

    def it_targets_the_npm_registry():
        assert NPM.url_template == "https://registry.npmjs.org/{name}"
