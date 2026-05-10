# Repo Name Checker

Check the availability of a repo name against the major package registries
(NPM, PyPI, crates.io).

## Usage

```
uvx repo-name-checker foobarbaz
```

Produces a table:

| Repository | Available | Collisions    |
| ---------- | :-------: | ------------- |
| npm        |     ❌    | dark-factory  |
| pypi       |     ✅    |               |
| crates     |     ✅    |               |

Pass a list of registries to narrow the check:

```
uvx repo-name-checker foobarbaz --registry npm --registry pypi
```

### Publish-time collision detection (npm)

npm rejects publishes whose normalized form (lowercased, with `-`/`_`/`.`
removed) matches an existing package. The `Collisions` column lists
existing names that would block your publish — for example `darkfactory`
collides with `dark-factory`. The check is best-effort: npm's exact
internal algorithm is private, so a passing check is necessary but not
sufficient.

### Output format

Use `--format` to choose the output. `table` is the default; `json` emits a
machine-readable list:

```
$ uvx repo-name-checker foobarbaz --format json
[
  {"registry": "npm", "name": "foobarbaz", "available": false, "collisions": ["foo-bar-baz"]},
  {"registry": "pypi", "name": "foobarbaz", "available": true, "collisions": []},
  {"registry": "crates", "name": "foobarbaz", "available": true, "collisions": []}
]
```

The CLI exits `0` if at least one registry has the name available, otherwise
`1`.

## SDK

The CLI is a thin wrapper over a Python SDK with 1:1 parity:

```python
import asyncio
from repo_name_checker import check, check_sync

# Async
results = asyncio.run(check("foobarbaz", registries=["npm", "pypi"]))

# Sync
results = check_sync("foobarbaz")

for r in results:
    print(r.registry, r.available)
```

## License

MIT
