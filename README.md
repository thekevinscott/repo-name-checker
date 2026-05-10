# Repo Name Checker

This checks for availability of a given repo name against registries.

## Usage

```
uvx repo-name-checker foobarbaz
```

Will produce a table:

| Repository | Available |
| NPM | ❌ |
| PyPI | ✅ |
| Crates | ✅ |

You can pass in a list of registries:

```
uvx repo-name-checker foobarbaz --registry npm --registry pypi
```

## License

MIT
