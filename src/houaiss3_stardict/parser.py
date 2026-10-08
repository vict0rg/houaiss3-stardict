# SPDX-License-Identifier: GPL-3.0-or-later
"""Line-oriented lexical record parser.

The parser contains structural format logic only. Repository tests use
synthetic records.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from .model import Block, Entry

_METADATA = {
    "T": ("metadata", "Rubrica"),
    "R": ("metadata", "Regionalismo"),
    "D": ("metadata", "Derivação"),
    "U": ("metadata", "Uso"),
    "I": ("metadata", "Uso"),
    "E": ("metadata", "Uso"),
    "L": ("metadata", "Língua"),
    "r": ("metadata", "Regência"),
    "c": ("metadata", "Classe gramatical"),
}

_GENERIC_NUMERIC_MARKERS = set("012456789")


def _part_of_speech_block(payload: str) -> Block:
    parts = [part.strip() for part in payload.split("|")]
    code = parts[0] if parts else ""

    if len(parts) >= 3:
        abbreviation = parts[1] or None
        text = "|".join(parts[2:]).strip()
    elif len(parts) == 2:
        abbreviation = None
        text = parts[1]
    else:
        abbreviation = None
        text = code

    return Block(
        kind="part_of_speech",
        text=text,
        abbreviation=abbreviation,
        code=code,
    )


def _metadata_block(prefix: str, payload: str) -> Block:
    kind, label = _METADATA[prefix]
    parts = [part.strip() for part in payload.split("|")]

    code = parts[0] if parts else ""
    abbreviation = None

    if len(parts) >= 3:
        abbreviation = parts[1] or None
        text = "|".join(parts[2:]).strip()
    elif len(parts) == 2:
        text = parts[1]
    else:
        text = code

    return Block(
        kind=kind,
        label=label,
        text=text,
        abbreviation=abbreviation,
        code=code,
    )


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

        if prefix in {"P", "$"}:
            alias = payload.strip()
            if alias:
                current.aliases.add(alias)
            continue

        if prefix == "d":
            current.blocks.append(Block(kind="date", text=payload.strip()))
            continue

        if prefix == "C":
            current.blocks.append(_part_of_speech_block(payload))
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
                Block(kind="etymology", label="Etimologia", text=payload.strip())
            )
            continue

        if prefix in _METADATA:
            current.blocks.append(_metadata_block(prefix, payload))
            continue

        if prefix == "o":
            current.blocks.append(
                Block(kind="metadata", label="Pronúncia", text=payload.strip())
            )
            continue

        if prefix in _GENERIC_NUMERIC_MARKERS:
            current.blocks.append(Block(kind="note", text=payload.strip()))
            continue

        if prefix in {"v", "S", "s", "®"}:
            meaningful = payload.strip()
            if meaningful and meaningful not in {"S", "N"}:
                current.blocks.append(Block(kind="note", text=meaningful))
            continue

        if prefix == "\\" and line.strip() == r"\par":
            continue

        current.blocks.append(Block(kind="note", text=payload.strip() or line.strip()))

    if current is not None and (limit is None or emitted < limit):
        yield current
