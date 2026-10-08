# SPDX-License-Identifier: GPL-3.0-or-later
"""StarDict writer and ordering helpers."""

from __future__ import annotations

import os
import shutil
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .model import RenderedEntry

CSS = r"""
.houaiss-group,
.houaiss-entry {
    font-size: 0.84em;
    line-height: 1.22;
    text-align: left !important;
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

.abbr,
.label,
.sense-number {
    font-weight: bold;
}

.definition {
    margin: 0.18em 0;
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
    multi_target_aliases: int
    dict_bytes: int
    idx_bytes: int


def _ascii_fold(data: bytes) -> bytes:
    return bytes(byte + 32 if 65 <= byte <= 90 else byte for byte in data)


def stardict_sort_key(value: str) -> tuple[bytes, bytes]:
    """Return a deterministic key matching StarDict's comparison behavior."""
    raw = value.encode("utf-8")
    return (_ascii_fold(raw), raw)


def _paths(root: Path, name: str) -> dict[str, Path]:
    return {
        suffix: root / f"{name}.{suffix}"
        for suffix in ("dict", "idx", "ifo", "syn", "css")
    }


def write_stardict(
    entries: list[RenderedEntry],
    output_dir: Path,
    name: str,
    *,
    overwrite: bool = False,
) -> WriteStats:
    """Write a StarDict dictionary using a staging directory."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    final_paths = _paths(output_dir, name)

    existing = [path for path in final_paths.values() if path.exists()]
    if existing and not overwrite:
        formatted = "\n".join(f"  {path}" for path in existing)
        raise FileExistsError(
            "Output files already exist. Use --overwrite to replace only the "
            f"selected output basename:\n{formatted}"
        )

    sorted_entries = sorted(entries, key=lambda item: stardict_sort_key(item.headword))

    stage = Path(tempfile.mkdtemp(prefix=f".{name}-build-", dir=output_dir))
    stage_paths = _paths(stage, name)

    try:
        idx_records: list[bytes] = []
        headword_to_index: dict[str, int] = {}
        dict_size = 0

        with stage_paths["dict"].open("wb") as dict_file:
            for index, entry in enumerate(sorted_entries):
                payload = entry.html.encode("utf-8")
                offset = dict_file.tell()
                dict_file.write(payload)
                dict_size += len(payload)

                idx_records.append(
                    entry.headword.encode("utf-8")
                    + b"\x00"
                    + struct.pack(">I", offset)
                    + struct.pack(">I", len(payload))
                )
                headword_to_index[entry.headword] = index

        with stage_paths["idx"].open("wb") as idx_file:
            for record in idx_records:
                idx_file.write(record)

        idx_size = stage_paths["idx"].stat().st_size

        alias_targets: dict[str, set[int]] = {}
        for entry in sorted_entries:
            target_index = headword_to_index[entry.headword]
            for alias in entry.aliases:
                alias = alias.strip()
                if not alias or alias == entry.headword:
                    continue
                alias_targets.setdefault(alias, set()).add(target_index)

        # Primary headwords always win over synonyms with identical spelling.
        for headword in headword_to_index:
            alias_targets.pop(headword, None)

        alias_pairs = sorted(
            (
                (alias, target)
                for alias, targets in alias_targets.items()
                for target in sorted(targets)
            ),
            key=lambda item: (stardict_sort_key(item[0]), item[1]),
        )

        if alias_pairs:
            with stage_paths["syn"].open("wb") as syn_file:
                for alias, target_index in alias_pairs:
                    syn_file.write(alias.encode("utf-8"))
                    syn_file.write(b"\x00")
                    syn_file.write(struct.pack(">I", target_index))

        ifo_lines = [
            "StarDict's dict ifo file",
            "version=3.0.0",
            f"bookname={name}",
            f"wordcount={len(sorted_entries)}",
            f"idxfilesize={idx_size}",
            "sametypesequence=h",
        ]
        if alias_pairs:
            ifo_lines.append(f"synwordcount={len(alias_pairs)}")

        stage_paths["ifo"].write_text("\n".join(ifo_lines) + "\n", encoding="utf-8")
        stage_paths["css"].write_text(CSS, encoding="utf-8")

        # Replace the selected basename only after every staged file is valid.
        for suffix in ("dict", "idx", "ifo", "css"):
            os.replace(stage_paths[suffix], final_paths[suffix])

        if stage_paths["syn"].exists():
            os.replace(stage_paths["syn"], final_paths["syn"])
        elif overwrite and final_paths["syn"].exists():
            final_paths["syn"].unlink()

        return WriteStats(
            wordcount=len(sorted_entries),
            synwordcount=len(alias_pairs),
            multi_target_aliases=sum(
                1 for targets in alias_targets.values() if len(targets) > 1
            ),
            dict_bytes=dict_size,
            idx_bytes=idx_size,
        )
    finally:
        shutil.rmtree(stage, ignore_errors=True)
