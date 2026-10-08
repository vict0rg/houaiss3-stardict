# SPDX-License-Identifier: GPL-3.0-or-later
"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .converter import convert_source, format_audit
from .stardict import write_stardict


def _project_root() -> Path:
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
        "--overwrite",
        action="store_true",
        help="Replace existing files with the selected output basename.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the complete parse and validation pipeline without writing output.",
    )
    parser.add_argument(
        "--no-morphemes",
        action="store_true",
        help="Do not include the auxiliary morpheme dictionary.",
    )
    parser.add_argument(
        "--no-verbal-aliases",
        action="store_true",
        help="Do not import validated verbal-form aliases.",
    )
    parser.add_argument(
        "--no-nominal-aliases",
        action="store_true",
        help="Do not generate conservative nominal inflection aliases.",
    )

    return parser


def _print_stats(stats: dict[str, int]) -> None:
    print(f"Main lexical records: {stats['main_records']:,}")
    print(f"Authoritative main search headwords: {stats['main_headwords']:,}")
    print(f"Morpheme records: {stats['morpheme_records']:,}")
    print(f"Morpheme search headwords: {stats['morpheme_headwords']:,}")
    print(f"Final search headwords: {stats['final_headwords']:,}")
    print(f"Explicit aliases: {stats['explicit_aliases']:,}")
    print(f"Verbal aliases added: {stats['verbal_aliases_added']:,}")
    print(f"Invalid verbal references: {stats['verbal_invalid_reference']:,}")
    print(f"Verbal cross-check mismatches: {stats['verbal_crosscheck_mismatch']:,}")
    print(f"Conservative nominal aliases added: {stats['nominal_aliases_added']:,}")
    print(f"Ambiguous nominal mappings skipped: {stats['nominal_ambiguous']:,}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.source is None:
        parser.error("SOURCE is required unless --version is used.")

    if not args.dry_run and args.output is None:
        parser.error("--output is required unless --dry-run is used.")

    source_dir = args.source.expanduser().resolve()
    if not source_dir.is_dir():
        parser.error(f"source directory does not exist: {source_dir}")

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

    print("Running full structural validation and conversion pipeline...")
    try:
        result = convert_source(
            source_dir,
            include_morphemes=not args.no_morphemes,
            include_verbal_aliases=not args.no_verbal_aliases,
            include_nominal_aliases=not args.no_nominal_aliases,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    _print_stats(result.stats)

    if args.dry_run:
        print("Dry run complete. No output files were written.")
        return

    assert output_dir is not None

    try:
        write_stats = write_stardict(
            result.rendered,
            output_dir,
            args.name,
            overwrite=args.overwrite,
        )
    except FileExistsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    audit_path = output_dir / f"{args.name}-audit.txt"
    audit_path.write_text(format_audit(result.stats), encoding="utf-8")

    print()
    print("StarDict conversion complete.")
    print(f"Output directory: {output_dir}")
    print(f"Output basename: {args.name}")
    print(f"Word count: {write_stats.wordcount:,}")
    print(f"Synonym/alias records: {write_stats.synwordcount:,}")
    print(f"Aliases with multiple targets: {write_stats.multi_target_aliases:,}")
    print(f"Dictionary bytes: {write_stats.dict_bytes:,}")
    print(f"Index bytes: {write_stats.idx_bytes:,}")
    print(f"Audit report: {audit_path}")
    print()
    print("Original source files were not modified.")
    print("No decoded intermediate files were created.")


if __name__ == "__main__":
    main()
