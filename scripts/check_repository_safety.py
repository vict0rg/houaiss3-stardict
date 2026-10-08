#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Reject file types and directories that must not enter the public repository."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_SUFFIXES = {
    ".dhn", ".dec", ".dict", ".idx", ".ifo", ".syn", ".mdx", ".mdd",
    ".dsl", ".db", ".sqlite", ".sqlite3", ".dump", ".bin", ".dat",
    ".zip", ".7z", ".rar", ".gif", ".bmp", ".jpg", ".jpeg", ".png",
    ".webp", ".tif", ".tiff",
}

FORBIDDEN_DIRECTORIES = {
    "data", "input", "output", "generated", "extracted", "decoded", "raw",
    "source-data", "raw-data", "decoded-data", "dictionary-data",
    "dictionary-output",
}

MAX_TRACKED_FILE_SIZE = 1024 * 1024
SIZE_EXCEPTIONS = {"LICENSE"}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    names = result.stdout.decode("utf-8").split("\0")
    return [ROOT / name for name in names if name]


def inspect(path: Path) -> list[str]:
    errors: list[str] = []
    rel = path.relative_to(ROOT)

    if any(part in FORBIDDEN_DIRECTORIES for part in rel.parts):
        errors.append(f"forbidden data directory: {rel}")

    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        errors.append(f"forbidden file type: {rel}")

    if not path.exists() or not path.is_file():
        return errors

    size = path.stat().st_size
    if size > MAX_TRACKED_FILE_SIZE and path.name not in SIZE_EXCEPTIONS:
        errors.append(f"unexpectedly large tracked file ({size} bytes): {rel}")

    return errors


def main() -> int:
    errors: list[str] = []

    try:
        files = tracked_files()
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: unable to inspect Git tracked files: {exc}")
        return 2

    for path in files:
        errors.extend(inspect(path))

    if errors:
        print("REPOSITORY SAFETY CHECK FAILED")
        print()
        for error in errors:
            print(f" - {error}")
        print()
        print("Remove the prohibited material before committing or pushing.")
        return 1

    print(f"Repository safety check passed: {len(files)} tracked files inspected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
