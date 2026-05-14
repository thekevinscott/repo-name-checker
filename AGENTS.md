# Agent Instructions

## Issue Tracking

This project uses **GitHub Issues**, not beads/bd. Do not run `bd init` here.

- File issues: https://github.com/thekevinscott/repo-name-checker/issues
- `gh issue list` / `gh issue create` from the CLI.

## Releases

Releases are driven by [putitoutthere](https://github.com/thekevinscott/putitoutthere) via `.github/workflows/release.yml`. Configuration lives in `putitoutthere.toml`. Versioning is dynamic via `hatch-vcs` — do not edit `[project].version` in `pyproject.toml`.

## Tooling

- Python: `uv` only. Never `pip`.
- Tests: `uv run pytest` (e2e tests are excluded by default; pass `-m e2e` to opt in).
