# SPDX-License-Identifier: GPL-3.0-or-later
"""Auxiliary lookup and optional morphology support."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .indexdata import DetailedIndexRecord, GroupIndexRecord, same_group_key


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


def parse_auxiliary_aliases(
    text: str,
    detailed: list[DetailedIndexRecord],
    grouped: list[GroupIndexRecord],
) -> tuple[dict[str, set[str]], dict[str, int]]:
    """Map auxiliary lookup forms to authoritative grouped search keys.

    The second numeric field selects a grouped search key using one-based
    indexing. The first numeric field is an auxiliary detailed-index reference.
    In the observed source data its convention is mixed: some rows validate
    against the zero-based adjacent record, some against the one-based adjacent
    record, and duplicate groups can make both valid.

    The grouped reference therefore selects the target. The detailed reference
    is used only as an independent structural cross-check. An alias is accepted
    only when at least one observed detailed-reference interpretation resolves
    to the same source-defined group.
    """
    by_target: dict[str, set[str]] = defaultdict(set)
    stats = {
        "rows": 0,
        "accepted_rows": 0,
        "self_alias_rows": 0,
        "invalid_reference": 0,
        "crosscheck_mismatch": 0,
        "p1_zero_only": 0,
        "p1_one_only": 0,
        "p1_both": 0,
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
            p1 = int(parts[1])
            p2 = int(parts[2])
        except ValueError:
            stats["invalid_reference"] += 1
            continue

        if not 1 <= p2 <= len(grouped):
            stats["invalid_reference"] += 1
            continue

        target = grouped[p2 - 1].key

        zero_match = (
            0 <= p1 < len(detailed)
            and same_group_key(detailed[p1].key, target)
        )
        one_match = (
            1 <= p1 <= len(detailed)
            and same_group_key(detailed[p1 - 1].key, target)
        )

        if zero_match and one_match:
            stats["p1_both"] += 1
        elif zero_match:
            stats["p1_zero_only"] += 1
        elif one_match:
            stats["p1_one_only"] += 1
        else:
            stats["crosscheck_mismatch"] += 1
            continue

        if not form:
            continue

        if form == target:
            stats["self_alias_rows"] += 1
            continue

        by_target[target].add(form)
        stats["accepted_rows"] += 1

    return dict(by_target), stats


def _nominal_candidates(word: str) -> list[str]:
    """Return conservative singular candidates for an optional heuristic."""
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
    """Infer unambiguous nominal aliases as an optional experiment."""
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
