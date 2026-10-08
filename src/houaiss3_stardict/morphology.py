# SPDX-License-Identifier: GPL-3.0-or-later
"""Morphological and alias mapping support."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .indexdata import DetailedIndexRecord, GroupIndexRecord


def parse_word_index(text: str) -> list[str]:
    """Extract the word column from a semicolon-delimited word index."""
    words: list[str] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line:
            continue
        parts = line.split(";")
        if len(parts) < 2:
            raise ValueError(f"Malformed word index row at line {line_no}.")
        words.append(parts[0])
    return words


def parse_verbal_aliases(
    text: str,
    detailed: list[DetailedIndexRecord],
    grouped: list[GroupIndexRecord],
) -> tuple[dict[str, set[str]], dict[str, int]]:
    """Map inflected forms to authoritative search headwords.

    The auxiliary verbal table stores two independent references. They are
    cross-checked before an alias is accepted.
    """
    by_target: dict[str, set[str]] = defaultdict(set)
    stats = {
        "rows": 0,
        "accepted": 0,
        "invalid_reference": 0,
        "crosscheck_mismatch": 0,
    }

    for line in text.splitlines():
        if not line:
            continue
        stats["rows"] += 1
        parts = line.split(";")
        if len(parts) < 4:
            stats["invalid_reference"] += 1
            continue

        form = parts[0].strip()
        try:
            detailed_zero_based = int(parts[1])
            grouped_one_based = int(parts[2])
        except ValueError:
            stats["invalid_reference"] += 1
            continue

        if not (
            0 <= detailed_zero_based < len(detailed)
            and 1 <= grouped_one_based <= len(grouped)
        ):
            stats["invalid_reference"] += 1
            continue

        detailed_key = detailed[detailed_zero_based].key
        grouped_key = grouped[grouped_one_based - 1].key

        if detailed_key != grouped_key:
            stats["crosscheck_mismatch"] += 1
            continue

        if form and form != grouped_key:
            by_target[grouped_key].add(form)
            stats["accepted"] += 1

    return dict(by_target), stats


def _nominal_candidates(word: str) -> list[str]:
    """Return conservative singular candidates for a surface form."""
    rules: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("ões", ("ão",)),
        ("ães", ("ão", "ãe")),
        ("ãos", ("ão",)),
        ("ais", ("al",)),
        ("éis", ("el",)),
        ("eis", ("el",)),
        ("óis", ("ol",)),
        ("uis", ("ul",)),
        ("ns", ("m",)),
        ("es", ("",)),
        ("s", ("",)),
    )

    candidates: list[str] = []
    seen: set[str] = set()

    for suffix, replacements in rules:
        if not word.endswith(suffix) or len(word) <= len(suffix):
            continue
        stem = word[: -len(suffix)]
        for replacement in replacements:
            candidate = stem + replacement
            if candidate and candidate not in seen:
                candidates.append(candidate)
                seen.add(candidate)

    return candidates


def build_conservative_nominal_aliases(
    surface_words: Iterable[str],
    headwords: set[str],
    occupied_aliases: set[str] | None = None,
) -> tuple[dict[str, set[str]], dict[str, int]]:
    """Infer only unambiguous nominal aliases backed by existing headwords."""
    occupied = occupied_aliases or set()
    by_target: dict[str, set[str]] = defaultdict(set)
    stats = {
        "surface_words": 0,
        "accepted": 0,
        "ambiguous": 0,
        "no_candidate": 0,
        "already_primary": 0,
        "already_mapped": 0,
    }

    for word in surface_words:
        stats["surface_words"] += 1

        if not word or word in headwords:
            stats["already_primary"] += 1
            continue

        if word in occupied:
            stats["already_mapped"] += 1
            continue

        matches = {
            candidate
            for candidate in _nominal_candidates(word)
            if candidate in headwords
        }

        if len(matches) == 1:
            target = next(iter(matches))
            by_target[target].add(word)
            stats["accepted"] += 1
        elif len(matches) > 1:
            stats["ambiguous"] += 1
        else:
            stats["no_candidate"] += 1

    return dict(by_target), stats
