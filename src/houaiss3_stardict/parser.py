# SPDX-License-Identifier: GPL-3.0-or-later
"""Line-oriented lexical record parser.

The parser contains structural format logic only. Repository tests use
synthetic records.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from .model import Block, Entry

_METADATA = {
    "T": ("metadata", "Field"),
    "R": ("metadata", "Regional usage"),
    "D": ("metadata", "Derivation"),
    "U": ("metadata", "Usage"),
    "I": ("metadata", "Historical usage"),
    "E": ("metadata", "Frequency"),
    "L": ("metadata", "Language"),
    "r": ("metadata", "Verb pattern"),
    "c": ("metadata", "Grammatical class"),
}

_GENERIC_NUMERIC_MARKERS = set("012456789")


def _pipe_block(prefix: str, payload: str) -> Block:
    parts = payload.split("|")
    code = parts[0].strip() if parts else ""
    abbreviation = parts[1].strip() if len(parts) > 1 else None
    text = parts[2].strip() if len(parts) > 2 else (
        parts[1].strip() if len(parts) > 1 else code
    )
    return Block(
        kind="part_of_speech",
        text=text,
        abbreviation=abbreviation,
        code=code,
    )


def _metadata_block(prefix: str, payload: str) -> Block:
    kind, label = _METADATA[prefix]
    parts = payload.split("|", 1)
    if len(parts) == 2:
        code, text = parts
    else:
        code, text = "", parts[0]
    return Block(kind=kind, label=label, text=text.strip(), code=code.strip())


def parse_entries(lines: Iterable[str], limit: int | None = None) -> Iterator[Entry]:
    """Parse decoded lines into source entries."""
    current: Entry | None = None
    pending_sense: str | None = None
    emitted = 0

    for raw_line in lines:
        line = raw_line.rstrip("\r\n")

        if not line:
            continue

        if line.startswith("EAH-"):
            continue

        if line.startswith("*"):
            if current is not None:
                yield current
                emitted += 1
                if limit is not None and emitted >= limit:
                    return

            current = Entry(headword=line[1:].strip())
            pending_sense = None
            continue

        if current is None:
            continue

        prefix = line[0]
        payload = line[1:]

        if prefix in {"A", "B"} and payload.isdigit():
            continue

        if prefix == "n" and payload.isdigit():
            current.homonym = payload
            continue

        if prefix == "P":
            alias = payload.strip()
            if alias:
                current.aliases.add(alias)
            continue

        if prefix == "$":
            alias = payload.strip()
            if alias:
                current.aliases.add(alias)
            continue

        if prefix == "d":
            current.blocks.append(Block(kind="date", text=payload.strip()))
            continue

        if prefix == "C":
            current.blocks.append(_pipe_block(prefix, payload))
            continue

        if prefix == "-":
            pending_sense = payload.strip()
            continue

        if prefix == ":":
            current.blocks.append(
                Block(
                    kind="definition",
                    text=payload.strip(),
                    number=pending_sense,
                )
            )
            pending_sense = None
            continue

        if prefix == "<":
            current.blocks.append(Block(kind="example", text=payload.strip()))
            continue

        if prefix == "#":
            current.blocks.append(Block(kind="subentry", text=payload.strip()))
            pending_sense = None
            continue

        if prefix == "!":
            current.blocks.append(Block(kind="note", text=payload.strip()))
            continue

        if prefix == "3":
            current.blocks.append(
                Block(kind="etymology", label="Etymology", text=payload.strip())
            )
            continue

        if prefix in _METADATA:
            current.blocks.append(_metadata_block(prefix, payload))
            continue

        if prefix == "o":
            current.blocks.append(
                Block(kind="metadata", label="Pronunciation", text=payload.strip())
            )
            continue

        if prefix in _GENERIC_NUMERIC_MARKERS:
            current.blocks.append(Block(kind="note", text=payload.strip()))
            continue

        if prefix in {"v", "S", "s", "®"}:
            # Compact flags used by auxiliary structures. They are preserved
            # only when they contain meaningful payload beyond a one-letter
            # flag value.
            meaningful = payload.strip()
            if meaningful and meaningful not in {"S", "N"}:
                current.blocks.append(Block(kind="note", text=meaningful))
            continue

        if prefix == "\\" and line.strip() == r"\par":
            continue

        # Preserve unclassified textual payload rather than silently deleting
        # information. The raw marker itself is not shown to users.
        current.blocks.append(Block(kind="note", text=payload.strip() or line.strip()))

    if current is not None and (limit is None or emitted < limit):
        yield current
