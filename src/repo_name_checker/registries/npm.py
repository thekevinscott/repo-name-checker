from repo_name_checker.registries.base import HttpStatusRegistry

NPM = HttpStatusRegistry(name="npm", url_template="https://registry.npmjs.org/{name}")
