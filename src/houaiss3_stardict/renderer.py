# SPDX-License-Identifier: GPL-3.0-or-later
"""HTML renderer for parsed lexical entries."""

from __future__ import annotations

import re

from .markup import inline_to_html
from .model import Entry, RenderedEntry

_SUBENTRY_SEPARATOR = re.compile(r"\s*[#@]\s*")


def _with_abbreviation(text: str, abbreviation: str | None) -> str:
    if not abbreviation:
        return text
    return f'<span class="abbr">{inline_to_html(abbreviation)}</span> — {text}'


def _subentry_to_html(text: str) -> str:
    """Render source alternative separators as a neutral slash."""
    normalized = _SUBENTRY_SEPARATOR.sub(" / ", text)
    return inline_to_html(normalized)


def render_entry(entry: Entry) -> str:
    """Render one decoded source record as an HTML fragment."""
    parts: list[str] = ['<div class="houaiss-entry">']

    title = inline_to_html(entry.headword)
    if entry.homonym:
        title += f'<sup class="homonym">{inline_to_html(entry.homonym)}</sup>'

    parts.append(f'<div class="headword">{title}</div>')

    for block in entry.blocks:
        if block.kind == "registered_trademark":
            parts.append(
                '<div class="metadata registered-trademark">'
                '<span class="label">Marca registrada</span></div>'
            )
            continue

        if block.kind == "subentry":
            text = _subentry_to_html(block.text)
        else:
            text = inline_to_html(block.text)

        if not text:
            continue

        if block.kind == "date":
            parts.append(
                f'<div class="metadata"><span class="label">Datação:</span> {text}</div>'
            )
        elif block.kind == "part_of_speech":
            parts.append(
                f'<div class="part-of-speech">'
                f'{_with_abbreviation(text, block.abbreviation)}</div>'
            )
        elif block.kind == "definition":
            number = (
                f'<span class="sense-number">{inline_to_html(block.number)}</span> '
                if block.number
                else ""
            )
            parts.append(f'<div class="definition">{number}{text}</div>')
        elif block.kind == "example":
            for example in [part.strip() for part in block.text.split("|") if part.strip()]:
                parts.append(f'<div class="example">{inline_to_html(example)}</div>')
        elif block.kind == "subentry":
            parts.append(f'<div class="subentry">{text}</div>')
        elif block.kind == "etymology":
            parts.append(
                f'<div class="etymology">'
                f'<span class="label">Etimologia:</span> {text}</div>'
            )
        elif block.kind == "metadata":
            label = inline_to_html(block.label or "Nota")
            value = _with_abbreviation(text, block.abbreviation)
            parts.append(
                f'<div class="metadata">'
                f'<span class="label">{label}:</span> {value}</div>'
            )
        else:
            parts.append(f'<div class="note">{text}</div>')

    parts.append("</div>")
    return "".join(parts)


def render_group(search_headword: str, entries: list[Entry]) -> RenderedEntry:
    """Render a validated search-key group while preserving display headwords."""
    aliases: set[str] = set()
    fragments: list[str] = []

    for entry in entries:
        aliases.update(entry.aliases)
        fragments.append(render_entry(entry))

    return RenderedEntry(
        headword=search_headword,
        html='<div class="houaiss-group">' + "".join(fragments) + "</div>",
        aliases=aliases,
    )
