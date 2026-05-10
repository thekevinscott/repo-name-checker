import argparse
from collections.abc import Sequence

from rich.console import Console
from rich.table import Table

from repo_name_checker.registries import REGISTRIES
from repo_name_checker.sdk import check_sync
from repo_name_checker.types import CheckResult


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
    return parser


def _render(results: list[CheckResult], console: Console) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Repository")
    table.add_column("Available", justify="center")
    for result in results:
        marker = "[green]✅[/green]" if result.available else "[red]❌[/red]"
        table.add_row(result.registry, marker)
    console.print(table)


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    results = check_sync(args.name, registries=args.registries)
    _render(results, Console())
    return 0 if any(r.available for r in results) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
