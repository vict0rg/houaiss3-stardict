# SPDX-License-Identifier: GPL-3.0-or-later
"""Minimal StarDict writer for HTML dictionary entries."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from .model import RenderedEntry

CSS = r"""
.houaiss-group,
.houaiss-entry {
    font-size: 0.84em;
    line-height: 1.22;
    text-align: left;
}

.houaiss-entry + .houaiss-entry {
    border-top: 1px solid;
    margin-top: 0.8em;
    padding-top: 0.6em;
}

.headword {
    font-size: 1.35em;
    font-weight: bold;
    margin: 0 0 0.18em 0;
}

.homonym {
    font-size: 0.68em;
    margin-left: 0.10em;
}

.part-of-speech {
    font-style: italic;
    margin: 0.08em 0 0.30em 0;
}

.abbr {
    font-weight: bold;
}

.definition {
    margin: 0.18em 0;
}

.sense-number {
    font-weight: bold;
}

.example {
    margin: 0.10em 0 0.10em 1.0em;
}

.subentry {
    font-weight: bold;
    margin: 0.55em 0 0.20em 0;
}

.metadata,
.note {
    margin: 0.10em 0;
}

.label {
    font-weight: bold;
}

.etymology {
    border-top: 1px solid;
    margin-top: 0.65em;
    padding-top: 0.40em;
}
""".strip() + "\n"


@dataclass(slots=True)
class WriteStats:
    wordcount: int
    synwordcount: int
    alias_conflicts: int
    dict_bytes: int
    idx_bytes: int


def _sort_key(value: str) -> bytes:
    return value.encode("utf-8")


def _target_paths(output_dir: Path, name: str) -> dict[str, Path]:
    return {
        suffix: output_dir / f"{name}.{suffix}"
        for suffix in ("dict", "idx", "ifo", "syn", "css")
    }


def write_stardict(
    entries: list[RenderedEntry],
    output_dir: Path,
    name: str,
    *,
    overwrite: bool = False,
) -> WriteStats:
    """Write StarDict files and return conversion statistics."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = _target_paths(output_dir, name)

    existing = [path for path in paths.values() if path.exists()]
    if existing and not overwrite:
        formatted = "\n".join(f"  {path}" for path in existing)
        raise FileExistsError(
            "Output files already exist. Use --overwrite to replace only the "
            f"selected output name:\n{formatted}"
        )

    sorted_entries = sorted(entries, key=lambda item: _sort_key(item.headword))

    idx_records: list[bytes] = []
    headword_to_index: dict[str, int] = {}
    dict_size = 0

    with paths["dict"].open("wb") as dict_file:
        for index, entry in enumerate(sorted_entries):
            payload = entry.html.encode("utf-8")
            offset = dict_file.tell()
            dict_file.write(payload)
            dict_size += len(payload)

            word = entry.headword.encode("utf-8")
            idx_records.append(
                word
                + b"\x00"
                + struct.pack(">I", offset)
                + struct.pack(">I", len(payload))
            )
            headword_to_index[entry.headword] = index

    with paths["idx"].open("wb") as idx_file:
        for record in idx_records:
            idx_file.write(record)

    idx_size = paths["idx"].stat().st_size

    alias_targets: dict[str, int] = {}
    alias_conflicts = 0

    for entry in sorted_entries:
        target_index = headword_to_index[entry.headword]

        for alias in entry.aliases:
            alias = alias.strip()
            if not alias or alias == entry.headword:
                continue

            previous = alias_targets.get(alias)
            if previous is None:
                alias_targets[alias] = target_index
            elif previous != target_index:
                alias_conflicts += 1

    # Primary headwords take precedence over aliases with the same spelling.
    for headword in headword_to_index:
        alias_targets.pop(headword, None)

    sorted_aliases = sorted(alias_targets.items(), key=lambda item: _sort_key(item[0]))

    if sorted_aliases:
        with paths["syn"].open("wb") as syn_file:
            for alias, target_index in sorted_aliases:
                syn_file.write(alias.encode("utf-8"))
                syn_file.write(b"\x00")
                syn_file.write(struct.pack(">I", target_index))
    elif paths["syn"].exists():
        paths["syn"].unlink()

    ifo_lines = [
        "StarDict's dict ifo file",
        "version=3.0.0",
        f"bookname={name}",
        f"wordcount={len(sorted_entries)}",
        f"idxfilesize={idx_size}",
        "sametypesequence=h",
    ]

    if sorted_aliases:
        ifo_lines.append(f"synwordcount={len(sorted_aliases)}")

    paths["ifo"].write_text("\n".join(ifo_lines) + "\n", encoding="utf-8")
    paths["css"].write_text(CSS, encoding="utf-8")

    return WriteStats(
        wordcount=len(sorted_entries),
        synwordcount=len(sorted_aliases),
        alias_conflicts=alias_conflicts,
        dict_bytes=dict_size,
        idx_bytes=idx_size,
    )
