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


class StarDictTests(unittest.TestCase):
    def test_writer_creates_core_files_and_synonyms(self) -> None:
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

            self.assertEqual(stats.wordcount, 2)
            self.assertEqual(stats.synwordcount, 3)
            self.assertEqual(stats.multi_target_aliases, 1)

            syn = (root / "Synthetic.syn").read_bytes()
            self.assertIn(b"alphas\x00", syn)
            self.assertEqual(syn.count(b"shared\x00"), 2)


if __name__ == "__main__":
    unittest.main()
