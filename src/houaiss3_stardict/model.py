# SPDX-License-Identifier: GPL-3.0-or-later
"""Neutral in-memory models used by the converter."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Block:
    """One structured piece of a lexical record."""

    kind: str
    text: str = ""
    label: str | None = None
    number: str | None = None
    abbreviation: str | None = None
    code: str | None = None


@dataclass(slots=True)
class Entry:
    """One decoded lexical record."""

    headword: str
    homonym: str | None = None
    blocks: list[Block] = field(default_factory=list)
    aliases: set[str] = field(default_factory=set)


@dataclass(slots=True)
class RenderedEntry:
    """One StarDict search headword with HTML and aliases."""

    headword: str
    html: str
    aliases: set[str] = field(default_factory=set)
