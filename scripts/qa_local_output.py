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

    unresolved_subentries = sum(
        1
        for value in subentries
        if re.search(r"(?<!&)#|@", value)
    )

    translation_labels = text.count(
        '<span class="label">Tradução:</span>'
    )
    registered_trademark_blocks = text.count(
        'class="metadata registered-trademark"'
    )

    print("Local output QA")
    print("===============")

    for key, value in checks.items():
        print(f"{key}: {value}")

    print(f"unresolved_subentry_separators: {unresolved_subentries}")
    print(f"translation_labels: {translation_labels}")
    print(f"registered_trademark_blocks: {registered_trademark_blocks}")

    if any(checks.values()):
        print("ERROR: unconverted low-level formatting controls were detected.")
        return 1

    if unresolved_subentries:
        print("ERROR: unresolved #/@ subentry separators were detected.")
        return 1

    print("Text-layer QA passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
