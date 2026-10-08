#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Validate the structure and ordering of a generated StarDict dictionary."""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from houaiss3_stardict.stardict import stardict_sort_key  # noqa: E402


def parse_ifo(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def parse_idx(path: Path) -> list[tuple[str, int, int]]:
    data = path.read_bytes()
    pos = 0
    records: list[tuple[str, int, int]] = []
    while pos < len(data):
        end = data.index(b"\x00", pos)
        word = data[pos:end].decode("utf-8")
        pos = end + 1
        if pos + 8 > len(data):
            raise ValueError("Truncated .idx record.")
        offset, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        records.append((word, offset, size))
    return records


def parse_syn(path: Path) -> list[tuple[str, int]]:
    data = path.read_bytes()
    pos = 0
    records: list[tuple[str, int]] = []
    while pos < len(data):
        end = data.index(b"\x00", pos)
        word = data[pos:end].decode("utf-8")
        pos = end + 1
        if pos + 4 > len(data):
            raise ValueError("Truncated .syn record.")
        target = struct.unpack(">I", data[pos : pos + 4])[0]
        pos += 4
        records.append((word, target))
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--name", default="Houaiss3")
    args = parser.parse_args()

    root = args.directory.expanduser().resolve()
    ifo = root / f"{args.name}.ifo"
    idx = root / f"{args.name}.idx"
    dict_path = root / f"{args.name}.dict"
    syn = root / f"{args.name}.syn"

    for path in (ifo, idx, dict_path):
        if not path.is_file():
            print(f"ERROR: missing file: {path}")
            return 2

    meta = parse_ifo(ifo)
    idx_records = parse_idx(idx)
    dict_size = dict_path.stat().st_size

    words = [word for word, _, _ in idx_records]
    if words != sorted(words, key=stardict_sort_key):
        print("ERROR: .idx is not sorted in StarDict order.")
        return 1

    for word, offset, size in idx_records:
        if offset + size > dict_size:
            print(f"ERROR: .idx record points beyond .dict: {word}")
            return 1

    declared_words = int(meta.get("wordcount", "-1"))
    if declared_words != len(idx_records):
        print(
            "ERROR: wordcount mismatch: "
            f"IFO={declared_words}, IDX={len(idx_records)}"
        )
        return 1

    syn_records: list[tuple[str, int]] = []
    if syn.is_file():
        syn_records = parse_syn(syn)
        syn_words = [word for word, _ in syn_records]
        if syn_words != sorted(syn_words, key=stardict_sort_key):
            print("ERROR: .syn is not sorted in StarDict order.")
            return 1
        for word, target in syn_records:
            if not 0 <= target < len(idx_records):
                print(f"ERROR: .syn target out of range: {word}")
                return 1

        declared_syns = int(meta.get("synwordcount", "-1"))
        if declared_syns != len(syn_records):
            print(
                "ERROR: synwordcount mismatch: "
                f"IFO={declared_syns}, SYN={len(syn_records)}"
            )
            return 1

    print("StarDict validation passed.")
    print(f"Headwords: {len(idx_records):,}")
    print(f"Synonym records: {len(syn_records):,}")
    print(f"Dictionary bytes: {dict_size:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
