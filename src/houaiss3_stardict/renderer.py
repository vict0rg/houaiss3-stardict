# SPDX-License-Identifier: GPL-3.0-or-later
"""HTML renderer for parsed lexical entries."""

from __future__ import annotations

from collections import OrderedDict

from .markup import inline_to_html
from .model import Entry, RenderedEntry


def render_entry(entry: Entry) -> str:
    """Render one parsed source record as an HTML fragment."""
    parts: list[str] = ['<div class="houaiss-entry">']

    title = inline_to_html(entry.headword)
    if entry.homonym:
        title += f'<sup class="homonym">{inline_to_html(entry.homonym)}</sup>'

    parts.append(f'<div class="headword">{title}</div>')

    for block in entry.blocks:
        text = inline_to_html(block.text)
        if not text:
            continue

        if block.kind == "date":
            parts.append(
                f'<div class="metadata"><span class="label">Dating:</span> {text}</div>'
            )

        elif block.kind == "part_of_speech":
            abbreviation = (
                f'<span class="abbr">{inline_to_html(block.abbreviation)}</span>'
                if block.abbreviation
                else ""
            )
            separator = " — " if abbreviation else ""
            parts.append(
                f'<div class="part-of-speech">{abbreviation}{separator}{text}</div>'
            )

        elif block.kind == "definition":
            number = (
                f'<span class="sense-number">{inline_to_html(block.number)}</span> '
                if block.number
                else ""
            )
            parts.append(f'<div class="definition">{number}{text}</div>')

        elif block.kind == "example":
            examples = [part.strip() for part in block.text.split("|") if part.strip()]
            for example in examples:
                parts.append(
                    f'<div class="example">{inline_to_html(example)}</div>'
                )

        elif block.kind == "subentry":
            parts.append(f'<div class="subentry">{text}</div>')

        elif block.kind == "etymology":
            parts.append(
                f'<div class="etymology"><span class="label">Etymology:</span> {text}</div>'
            )

        elif block.kind == "metadata":
            label = inline_to_html(block.label or "Note")
            parts.append(
                f'<div class="metadata"><span class="label">{label}:</span> {text}</div>'
            )

        else:
            parts.append(f'<div class="note">{text}</div>')

    parts.append("</div>")
    return "".join(parts)


def group_and_render(entries: list[Entry]) -> list[RenderedEntry]:
    """Group exact duplicate headwords while preserving homonym records."""
    grouped: OrderedDict[str, list[Entry]] = OrderedDict()

    for entry in entries:
        grouped.setdefault(entry.headword, []).append(entry)

    output: list[RenderedEntry] = []

    for headword, records in grouped.items():
        aliases: set[str] = set()
        fragments: list[str] = []

        for record in records:
            aliases.update(record.aliases)
            fragments.append(render_entry(record))

        output.append(
            RenderedEntry(
                headword=headword,
                html='<div class="houaiss-group">' + "".join(fragments) + "</div>",
                aliases=aliases,
            )
        )

    return output
