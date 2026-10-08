# SPDX-License-Identifier: GPL-3.0-or-later
"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .decoder import read_decoded_text
from .parser import parse_entries
from .renderer import group_and_render
from .stardict import write_stardict


def _project_root() -> Path:
    # In an editable checkout:
    # repo/src/houaiss3_stardict/cli.py -> repo
    return Path(__file__).resolve().parents[2]


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="houaiss3-stardict",
        description=(
            "Educational legacy dictionary interoperability and "
            "StarDict conversion tool. Source files are read-only."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        help="Directory containing user-supplied source files.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Directory where locally generated StarDict files will be written.",
    )

    parser.add_argument(
        "--name",
        default="Houaiss3",
        help="Output basename. Default: Houaiss3",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Convert only the first N source records for local testing.",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing files with the selected output basename.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse source records and report counts without writing output.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.source is None:
        parser.error("SOURCE is required unless --version is used.")

    if not args.dry_run and args.output is None:
        parser.error("--output is required unless --dry-run is used.")

    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be greater than zero.")

    source_dir = args.source.expanduser().resolve()
    if not source_dir.is_dir():
        parser.error(f"source directory does not exist: {source_dir}")

    source_file = source_dir / "deah001.dhn"
    if not source_file.is_file():
        parser.error(f"required source file was not found: {source_file}")

    repo_root = _project_root()
    if _inside(source_dir, repo_root):
        parser.error("source dictionary data must not be stored inside the repository.")

    output_dir: Path | None = None
    if args.output is not None:
        output_dir = args.output.expanduser().resolve()
        if _inside(output_dir, repo_root):
            parser.error("generated dictionary data must not be written inside the repository.")
        if output_dir == source_dir:
            parser.error("output directory must be different from the source directory.")

    print("Reading source data in memory...")
    decoded_text = read_decoded_text(source_file)

    print("Parsing lexical records...")
    entries = list(parse_entries(decoded_text.splitlines(), limit=args.limit))
    rendered = group_and_render(entries)

    alias_count = sum(len(entry.aliases) for entry in rendered)

    print(f"Source records parsed: {len(entries):,}")
    print(f"StarDict headwords after exact grouping: {len(rendered):,}")
    print(f"Explicit aliases collected from source records: {alias_count:,}")

    if args.dry_run:
        print("Dry run complete. No output files were written.")
        return

    assert output_dir is not None

    try:
        stats = write_stardict(
            rendered,
            output_dir,
            args.name,
            overwrite=args.overwrite,
        )
    except FileExistsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print()
    print("StarDict conversion complete.")
    print(f"Output directory: {output_dir}")
    print(f"Output basename: {args.name}")
    print(f"Word count: {stats.wordcount:,}")
    print(f"Synonym/alias count: {stats.synwordcount:,}")
    print(f"Alias conflicts ignored: {stats.alias_conflicts:,}")
    print(f"Dictionary bytes: {stats.dict_bytes:,}")
    print(f"Index bytes: {stats.idx_bytes:,}")
    print()
    print("Original source files were not modified.")
    print("No decoded intermediate files were created.")


if __name__ == "__main__":
    main()
