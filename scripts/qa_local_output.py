#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run content-free quality checks on a locally generated StarDict file."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dictionary", type=Path)
    args = parser.parse_args()

    path = args.dictionary.expanduser().resolve()

    if not path.is_file():
        print(f"ERROR: dictionary file not found: {path}")
        return 2

    data = path.read_bytes()
    text = data.decode("utf-8", errors="strict")

    checks = {
        "raw_rtf_group_prefix": data.count(b"{\\"),
        "raw_rtf_paragraph_control": data.count(b"\\par"),
        "nul_bytes_in_html": data.count(b"\x00"),
    }

    subentries = re.findall(
        r'<div class="subentry">(.*?)</div>',
        text,
        flags=re.DOTALL,
    )
    suspicious_subentries = sum(
        1 for value in subentries
        if "#" in value or " @ " in value
    )

    print("Local output QA")
    print("===============")

    for key, value in checks.items():
        print(f"{key}: {value}")

    print(
        "subentries_with_embedded_hash_or_at_markers: "
        f"{suspicious_subentries}"
    )

    if any(checks.values()):
        print("ERROR: unconverted low-level formatting controls were detected.")
        return 1

    print("Core markup QA passed.")

    if suspicious_subentries:
        print(
            "NOTE: Some source subentry strings contain embedded lexical "
            "separators. They are preserved rather than guessed."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
