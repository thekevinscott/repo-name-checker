import argparse
import dataclasses
import json
from collections.abc import Sequence

from rich.console import Console
from rich.table import Table

from repo_name_checker.registries import REGISTRIES
from repo_name_checker.sdk import check_sync
from repo_name_checker.types import CheckResult

FORMATS = ("table", "json")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-name-checker",
        description="Check whether a repo name is available across package registries.",
    )
    parser.add_argument("name", help="Name to check")
    parser.add_argument(
        "--registry",
        action="append",
        choices=sorted(REGISTRIES),
        dest="registries",
        help="Registry to check (repeatable). Defaults to all known registries.",
    )
    parser.add_argument(
        "--format",
        choices=FORMATS,
        default="table",
        dest="output_format",
        help="Output format (default: table).",
    )
    return parser


def _render_table(results: list[CheckResult], console: Console) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Repository")
    table.add_column("Available", justify="center")
    table.add_column("Collisions")
    for result in results:
        marker = "[green]✅[/green]" if result.available else "[red]❌[/red]"
        collisions = ", ".join(result.collisions) if result.collisions else ""
        table.add_row(result.registry, marker, collisions)
    console.print(table)


def _render_json(results: list[CheckResult], console: Console) -> None:
    payload = [dataclasses.asdict(r) for r in results]
    for entry in payload:
        entry["collisions"] = list(entry["collisions"])
    console.print_json(json.dumps(payload))


_RENDERERS = {"table": _render_table, "json": _render_json}


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    results = check_sync(args.name, registries=args.registries)
    _RENDERERS[args.output_format](results, Console())
    return 0 if any(r.available for r in results) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
