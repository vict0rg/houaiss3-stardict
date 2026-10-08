# SPDX-License-Identifier: GPL-3.0-or-later
"""Parsers and validators for auxiliary lexical index structures."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from .model import Entry


@dataclass(frozen=True, slots=True)
class DetailedIndexRecord:
    key: str
    ordinal: int
    homonym: int
    kind: str


@dataclass(frozen=True, slots=True)
class GroupIndexRecord:
    key: str
    start: int
    duplicate_count: int
    kind: str

    @property
    def span(self) -> int:
        """Return the number of detailed rows represented by this group."""
        return self.duplicate_count if self.duplicate_count > 0 else 1


def _fields(line: str) -> list[str]:
    return line.rstrip("\r\n").split(";")


def _normalized_group_key(value: str) -> str:
    """Normalize a source search key for group-membership validation.

    The grouped source index can deliberately collapse capitalization variants
    into one searchable key. NFC + Unicode case folding is used only to verify
    membership inside source-defined group boundaries. It does not invent new
    groups and does not alter the authoritative grouped search key.
    """
    return unicodedata.normalize("NFC", value).casefold()


def same_group_key(left: str, right: str) -> bool:
    """Return whether two source keys belong to the same indexed group."""
    return _normalized_group_key(left) == _normalized_group_key(right)


def parse_detailed_index(text: str) -> list[DetailedIndexRecord]:
    records: list[DetailedIndexRecord] = []

    for line_no, line in enumerate(text.splitlines(), 1):
        if not line:
            continue

        parts = _fields(line)
        if len(parts) < 4:
            raise ValueError(f"Malformed detailed index row at line {line_no}.")

        try:
            ordinal = int(parts[1])
            homonym = int(parts[2])
        except ValueError as exc:
            raise ValueError(
                f"Invalid numeric field in detailed index at line {line_no}."
            ) from exc

        records.append(
            DetailedIndexRecord(
                key=parts[0],
                ordinal=ordinal,
                homonym=homonym,
                kind=parts[3],
            )
        )

    return records


def parse_group_index(text: str) -> list[GroupIndexRecord]:
    records: list[GroupIndexRecord] = []

    for line_no, line in enumerate(text.splitlines(), 1):
        if not line:
            continue

        parts = _fields(line)
        if len(parts) < 4:
            raise ValueError(f"Malformed grouped index row at line {line_no}.")

        try:
            start = int(parts[1])
            duplicate_count = int(parts[2])
        except ValueError as exc:
            raise ValueError(
                f"Invalid numeric field in grouped index at line {line_no}."
            ) from exc

        records.append(
            GroupIndexRecord(
                key=parts[0],
                start=start,
                duplicate_count=duplicate_count,
                kind=parts[3],
            )
        )

    return records


def build_authoritative_groups(
    entries: list[Entry],
    detailed: list[DetailedIndexRecord],
    grouped: list[GroupIndexRecord],
) -> list[tuple[str, list[Entry]]]:
    """Build search groups using the source application's own indexes.

    Group boundaries, start positions, and group sizes come exclusively from
    the grouped index. The detailed index independently verifies those spans.

    Capitalization differences inside a source-defined group are valid. The
    grouped key remains the authoritative StarDict search key while each
    lexical record retains its original display headword.
    """
    if len(entries) != len(detailed):
        raise ValueError(
            "Entry/index count mismatch: "
            f"{len(entries):,} decoded records vs {len(detailed):,} index rows."
        )

    for expected, record in enumerate(detailed, 1):
        if record.ordinal != expected:
            raise ValueError(
                "Detailed index ordinal mismatch at row "
                f"{expected}: stored ordinal={record.ordinal}."
            )

    result: list[tuple[str, list[Entry]]] = []
    expected_start = 1

    for row_no, group in enumerate(grouped, 1):
        if group.start != expected_start:
            raise ValueError(
                "Grouped index has a gap or overlap at row "
                f"{row_no}: expected start {expected_start}, got {group.start}."
            )

        start = group.start - 1
        end = start + group.span

        if end > len(entries):
            raise ValueError(
                f"Grouped index row {row_no} extends beyond the record table."
            )

        detailed_slice = detailed[start:end]
        mismatches = [
            record.key
            for record in detailed_slice
            if not same_group_key(record.key, group.key)
        ]

        if mismatches:
            sample = ", ".join(repr(value) for value in mismatches[:3])
            raise ValueError(
                "Grouped/detailed index key mismatch at grouped row "
                f"{row_no}: grouped key={group.key!r}, "
                f"detailed mismatch sample={sample}."
            )

        result.append((group.key, entries[start:end]))
        expected_start = end + 1

    covered = expected_start - 1
    if covered != len(entries):
        raise ValueError(
            "Grouped index does not cover all decoded records: "
            f"covered {covered:,} of {len(entries):,}."
        )

    return result


def parse_offset_index_keys(text: str) -> list[str]:
    """Return the key column from a key-to-offset index."""
    keys: list[str] = []

    for line_no, line in enumerate(text.splitlines(), 1):
        if not line:
            continue

        parts = _fields(line)
        if len(parts) < 2:
            raise ValueError(f"Malformed offset index row at line {line_no}.")

        keys.append(parts[0])

    return keys


def group_parallel_entries(
    entries: list[Entry],
    index_keys: list[str],
) -> list[tuple[str, list[Entry]]]:
    """Group records using an equally sized parallel search-key index."""
    if len(entries) != len(index_keys):
        raise ValueError(
            "Parallel index count mismatch: "
            f"{len(entries):,} records vs {len(index_keys):,} index rows."
        )

    order: list[str] = []
    grouped: dict[str, list[Entry]] = {}

    for key, entry in zip(index_keys, entries, strict=True):
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(entry)

    return [(key, grouped[key]) for key in order]
