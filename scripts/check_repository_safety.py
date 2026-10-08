#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Protect the public repository from proprietary or generated dictionary data.

The checker inspects the Git index itself, not just worktree files. This is
important for pre-commit use because a staged blob can differ from the current
worktree copy of the same path.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_ENDINGS = (
    ".dhn",
    ".dec",
    ".dict",
    ".dict.dz",
    ".idx",
    ".idx.oft",
    ".ifo",
    ".syn",
    ".mdx",
    ".mdd",
    ".dsl",
    ".dsl.dz",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".dump",
    ".bin",
    ".dat",
    ".zip",
    ".7z",
    ".rar",
    ".tar",
    ".tar.gz",
    ".tgz",
    ".gif",
    ".bmp",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".tif",
    ".tiff",
    ".patch",
    ".diff",
)

FORBIDDEN_DIRECTORIES = {
    "data",
    "input",
    "output",
    "generated",
    "extracted",
    "decoded",
    "raw",
    "source-data",
    "raw-data",
    "decoded-data",
    "dictionary-data",
    "dictionary-output",
}

FORBIDDEN_GENERATED_NAMES = {
    "houaiss3-audit.txt",
}

MAX_INDEXED_BLOB_SIZE = 1024 * 1024
SIZE_EXCEPTIONS = {"LICENSE"}

BINARY_SIGNATURES = (
    (b"GIF87a", "GIF"),
    (b"GIF89a", "GIF"),
    (b"\x89PNG\r\n\x1a\n", "PNG"),
    (b"\xff\xd8\xff", "JPEG"),
    (b"BM", "BMP"),
    (b"PK\x03\x04", "ZIP"),
    (b"Rar!\x1a\x07", "RAR"),
    (b"7z\xbc\xaf\x27\x1c", "7-Zip"),
    (b"\x1f\x8b", "gzip"),
    (b"SQLite format 3\x00", "SQLite"),
    (b"StarDict's dict ifo file", "StarDict IFO"),
)

SOURCE_STYLE_BASENAME = re.compile(r"^deah\d{3}(?:[._-]|$)", re.IGNORECASE)

# These are intentionally generic structural heuristics. They do not contain
# or depend on any real dictionary lexical strings.
LEXICAL_MARKERS = set("*ABnCP$-:<#dTRDUr3!IELM012456789®")


@dataclass(frozen=True, slots=True)
class IndexEntry:
    mode: str
    object_id: str
    stage: int
    path: PurePosixPath


def _run_git(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        env=os.environ.copy(),
    ).stdout


def index_entries() -> list[IndexEntry]:
    """Return stage-zero paths and object IDs from the active Git index."""
    raw = _run_git("ls-files", "-s", "-z")
    entries: list[IndexEntry] = []

    for record in raw.split(b"\x00"):
        if not record:
            continue

        metadata, separator, path_bytes = record.partition(b"\t")
        if not separator:
            raise ValueError("Malformed git ls-files record.")

        fields = metadata.decode("ascii").split()
        if len(fields) != 3:
            raise ValueError("Malformed git ls-files metadata.")

        mode, object_id, stage_text = fields
        path = PurePosixPath(path_bytes.decode("utf-8", errors="surrogateescape"))

        entries.append(
            IndexEntry(
                mode=mode,
                object_id=object_id,
                stage=int(stage_text),
                path=path,
            )
        )

    return entries


def inspect_path(path: PurePosixPath) -> list[str]:
    """Check an indexed repository path without consulting the worktree."""
    errors: list[str] = []
    lowered_parts = [part.casefold() for part in path.parts]
    lowered_name = path.name.casefold()

    if any(part in FORBIDDEN_DIRECTORIES for part in lowered_parts):
        errors.append(f"forbidden data directory: {path}")

    if lowered_name.endswith(FORBIDDEN_ENDINGS):
        errors.append(f"forbidden file type: {path}")

    if SOURCE_STYLE_BASENAME.match(path.name):
        errors.append(f"source-style dictionary filename: {path}")

    if lowered_name in FORBIDDEN_GENERATED_NAMES or lowered_name.endswith(
        "-audit.txt"
    ):
        errors.append(f"generated dictionary audit file: {path}")

    return errors


def _looks_like_lexical_stream(text: str) -> bool:
    lines = [line for line in text.splitlines() if line]

    if len(lines) < 80:
        return False

    marked = [
        line
        for line in lines
        if line and not line[0].isspace() and line[0] in LEXICAL_MARKERS
    ]
    markers = {line[0] for line in marked}

    return (
        len(marked) >= 60
        and len(marked) / len(lines) >= 0.75
        and "*" in markers
        and ":" in markers
        and len(markers) >= 6
    )


def _looks_like_dictionary_index(text: str) -> bool:
    lines = [line for line in text.splitlines() if line]

    if len(lines) < 60:
        return False

    structured = [
        line
        for line in lines
        if line.count(";") >= 3 and len(line) <= 4096
    ]

    return len(structured) >= 50 and len(structured) / len(lines) >= 0.80


def inspect_blob(
    path: PurePosixPath,
    blob: bytes,
    *,
    declared_size: int | None = None,
) -> list[str]:
    """Inspect the exact staged blob content for one indexed path."""
    errors: list[str] = []
    size = len(blob) if declared_size is None else declared_size

    if size > MAX_INDEXED_BLOB_SIZE and path.name not in SIZE_EXCEPTIONS:
        errors.append(f"unexpectedly large indexed blob ({size} bytes): {path}")
        return errors

    for signature, label in BINARY_SIGNATURES:
        if blob.startswith(signature):
            errors.append(f"forbidden {label} content signature: {path}")
            break

    if b"\x00" in blob:
        errors.append(f"binary NUL byte in indexed blob: {path}")
        return errors

    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError:
        errors.append(f"non-UTF-8 indexed blob: {path}")
        return errors

    if _looks_like_lexical_stream(text):
        errors.append(f"source-like lexical record stream: {path}")

    if _looks_like_dictionary_index(text):
        errors.append(f"dictionary-index-like text structure: {path}")

    return errors


def blob_size(object_id: str) -> int:
    return int(_run_git("cat-file", "-s", object_id).decode("ascii").strip())


def blob_bytes(object_id: str) -> bytes:
    return _run_git("cat-file", "blob", object_id)


def inspect_index_entry(entry: IndexEntry) -> list[str]:
    errors = inspect_path(entry.path)

    if entry.stage != 0:
        errors.append(f"unmerged Git index stage {entry.stage}: {entry.path}")
        return errors

    # Gitlinks and other non-blob modes are not expected in this small
    # source-only repository. Reject them rather than assuming they are safe.
    if entry.mode not in {"100644", "100755"}:
        errors.append(f"unexpected Git index mode {entry.mode}: {entry.path}")
        return errors

    size = blob_size(entry.object_id)

    if size > MAX_INDEXED_BLOB_SIZE and entry.path.name not in SIZE_EXCEPTIONS:
        errors.append(
            f"unexpectedly large indexed blob ({size} bytes): {entry.path}"
        )
        return errors

    blob = blob_bytes(entry.object_id)
    errors.extend(inspect_blob(entry.path, blob, declared_size=size))
    return errors


def main() -> int:
    try:
        entries = index_entries()
    except (subprocess.CalledProcessError, ValueError) as exc:
        print(f"ERROR: unable to inspect the Git index: {exc}")
        return 2

    errors: list[str] = []

    for entry in entries:
        errors.extend(inspect_index_entry(entry))

    # Keep diagnostics deterministic and avoid duplicate messages.
    errors = sorted(set(errors))

    if errors:
        print("REPOSITORY SAFETY CHECK FAILED")
        print()
        for error in errors:
            print(f" - {error}")
        print()
        print(
            "Remove prohibited material from the Git index before committing "
            "or pushing."
        )
        return 1

    print(
        "Repository safety check passed: "
        f"{len(entries)} indexed blobs inspected."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
