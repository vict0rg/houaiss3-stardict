# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic StarDict writer tests."""

import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from houaiss3_stardict.model import RenderedEntry  # noqa: E402
from houaiss3_stardict.stardict import write_stardict  # noqa: E402


def parse_idx(path: Path) -> list[tuple[str, int, int]]:
    data = path.read_bytes()
    pos = 0
    records: list[tuple[str, int, int]] = []

    while pos < len(data):
        end = data.index(b"\x00", pos)
        word = data[pos:end].decode("utf-8")
        pos = end + 1
        offset, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        records.append((word, offset, size))

    return records


class StarDictTests(unittest.TestCase):
    def test_writer_materializes_multi_target_aliases(self) -> None:
        entries = [
            RenderedEntry(
                headword="alpha",
                html="<b>synthetic alpha</b>",
                aliases={"alphas", "shared"},
            ),
            RenderedEntry(
                headword="beta",
                html="<b>synthetic beta</b>",
                aliases={"shared"},
            ),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stats = write_stardict(entries, root, "Synthetic")

            self.assertEqual(stats.wordcount, 3)
            self.assertEqual(stats.synwordcount, 1)
            self.assertEqual(stats.multi_target_aliases, 1)

            syn = (root / "Synthetic.syn").read_bytes()
            self.assertIn(b"alphas\x00", syn)
            self.assertNotIn(b"shared\x00", syn)

            idx = parse_idx(root / "Synthetic.idx")
            shared = [record for record in idx if record[0] == "shared"]
            self.assertEqual(len(shared), 1)

            _, offset, size = shared[0]
            payload = (root / "Synthetic.dict").read_bytes()[offset : offset + size]

            self.assertIn(b"synthetic alpha", payload)
            self.assertIn(b"synthetic beta", payload)

    def test_primary_headword_wins_over_same_spelling_alias(self) -> None:
        entries = [
            RenderedEntry(
                headword="alpha",
                html="<b>synthetic alpha</b>",
                aliases=set(),
            ),
            RenderedEntry(
                headword="beta",
                html="<b>synthetic beta</b>",
                aliases={"alpha"},
            ),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stats = write_stardict(entries, root, "Synthetic")

            self.assertEqual(stats.wordcount, 2)
            self.assertEqual(stats.synwordcount, 0)

            idx = parse_idx(root / "Synthetic.idx")
            self.assertEqual([word for word, _, _ in idx].count("alpha"), 1)
            self.assertFalse((root / "Synthetic.syn").exists())


if __name__ == "__main__":
    unittest.main()
