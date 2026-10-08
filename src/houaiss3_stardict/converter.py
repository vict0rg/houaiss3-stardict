# SPDX-License-Identifier: GPL-3.0-or-later
"""High-level conversion pipeline."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

from .decoder import read_decoded_text
from .indexdata import (
    build_authoritative_groups,
    group_parallel_entries,
    parse_detailed_index,
    parse_group_index,
    parse_offset_index_keys,
)
from .model import Entry, RenderedEntry
from .morphology import (
    build_conservative_nominal_aliases,
    parse_verbal_aliases,
    parse_word_index,
)
from .parser import parse_entries
from .renderer import render_group


@dataclass(slots=True)
class ConversionResult:
    rendered: list[RenderedEntry]
    stats: dict[str, int]


def _read(source_dir: Path, number: int) -> str:
    path = source_dir / f"deah{number:03d}.dhn"
    if not path.is_file():
        raise FileNotFoundError(f"Required source file was not found: {path}")
    return read_decoded_text(path)


def _merge_aliases(
    rendered_by_key: dict[str, RenderedEntry],
    mapping: dict[str, set[str]],
) -> int:
    added = 0
    for target, aliases in mapping.items():
        entry = rendered_by_key.get(target)
        if entry is None:
            continue
        before = len(entry.aliases)
        entry.aliases.update(aliases)
        added += len(entry.aliases) - before
    return added


def convert_source(
    source_dir: Path,
    *,
    include_morphemes: bool = True,
    include_verbal_aliases: bool = True,
    include_nominal_aliases: bool = True,
) -> ConversionResult:
    """Decode, validate, parse, enrich, and render local source data."""
    source_dir = Path(source_dir)

    main_text = _read(source_dir, 1)
    group_text = _read(source_dir, 16)
    detailed_text = _read(source_dir, 17)

    main_entries = list(parse_entries(main_text.splitlines()))
    grouped_index = parse_group_index(group_text)
    detailed_index = parse_detailed_index(detailed_text)

    main_groups = build_authoritative_groups(
        main_entries,
        detailed_index,
        grouped_index,
    )

    combined: OrderedDict[str, list[Entry]] = OrderedDict(main_groups)
    main_keys = set(combined)

    stats: dict[str, int] = {
        "main_records": len(main_entries),
        "main_headwords": len(main_groups),
        "morpheme_records": 0,
        "morpheme_headwords": 0,
        "final_headwords": 0,
        "explicit_aliases": 0,
        "verbal_aliases_added": 0,
        "nominal_aliases_added": 0,
        "verbal_rows": 0,
        "verbal_invalid_reference": 0,
        "verbal_crosscheck_mismatch": 0,
        "nominal_surface_words": 0,
        "nominal_ambiguous": 0,
    }

    if include_morphemes:
        morph_text = _read(source_dir, 7)
        morph_index_text = _read(source_dir, 8)
        morph_entries = list(parse_entries(morph_text.splitlines()))
        morph_keys = parse_offset_index_keys(morph_index_text)
        morph_groups = group_parallel_entries(morph_entries, morph_keys)

        stats["morpheme_records"] = len(morph_entries)
        stats["morpheme_headwords"] = len(morph_groups)

        for key, entries in morph_groups:
            combined.setdefault(key, []).extend(entries)

    rendered = [
        render_group(search_headword=key, entries=entries)
        for key, entries in combined.items()
    ]
    rendered_by_key = {entry.headword: entry for entry in rendered}

    stats["final_headwords"] = len(rendered)

    explicit_forms: set[str] = set()
    for entry in rendered:
        explicit_forms.update(entry.aliases)
    stats["explicit_aliases"] = sum(len(entry.aliases) for entry in rendered)

    if include_verbal_aliases:
        verbal_text = _read(source_dir, 18)
        verbal_map, verbal_stats = parse_verbal_aliases(
            verbal_text,
            detailed_index,
            grouped_index,
        )
        stats["verbal_rows"] = verbal_stats["rows"]
        stats["verbal_invalid_reference"] = verbal_stats["invalid_reference"]
        stats["verbal_crosscheck_mismatch"] = verbal_stats["crosscheck_mismatch"]
        stats["verbal_aliases_added"] = _merge_aliases(rendered_by_key, verbal_map)
        for aliases in verbal_map.values():
            explicit_forms.update(aliases)

    if include_nominal_aliases:
        words_text = _read(source_dir, 6)
        surface_words = parse_word_index(words_text)
        nominal_map, nominal_stats = build_conservative_nominal_aliases(
            surface_words,
            main_keys,
            occupied_aliases=explicit_forms,
        )
        stats["nominal_surface_words"] = nominal_stats["surface_words"]
        stats["nominal_ambiguous"] = nominal_stats["ambiguous"]
        stats["nominal_aliases_added"] = _merge_aliases(
            rendered_by_key,
            nominal_map,
        )

    return ConversionResult(rendered=rendered, stats=stats)


def format_audit(stats: dict[str, int]) -> str:
    """Return a content-free audit report containing counts only."""
    lines = [
        "houaiss3-stardict local conversion audit",
        "========================================",
        "",
        f"Main lexical records: {stats['main_records']:,}",
        f"Authoritative main search headwords: {stats['main_headwords']:,}",
        f"Morpheme records: {stats['morpheme_records']:,}",
        f"Morpheme search headwords: {stats['morpheme_headwords']:,}",
        f"Final StarDict headwords before writing: {stats['final_headwords']:,}",
        "",
        f"Explicit aliases from lexical records: {stats['explicit_aliases']:,}",
        f"Verbal auxiliary rows inspected: {stats['verbal_rows']:,}",
        f"Verbal aliases added: {stats['verbal_aliases_added']:,}",
        f"Invalid verbal references: {stats['verbal_invalid_reference']:,}",
        f"Verbal cross-check mismatches: {stats['verbal_crosscheck_mismatch']:,}",
        f"Nominal surface words inspected: {stats['nominal_surface_words']:,}",
        f"Conservative nominal aliases added: {stats['nominal_aliases_added']:,}",
        f"Ambiguous nominal mappings skipped: {stats['nominal_ambiguous']:,}",
        "",
        "No lexical content is included in this report.",
    ]
    return "\n".join(lines) + "\n"
