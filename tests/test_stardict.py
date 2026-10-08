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
    def test_writer_creates_core_files_and_synonym(self) -> None:
        entries = [
            RenderedEntry(
                headword="alpha",
                html="<b>synthetic alpha</b>",
                aliases={"alphas"},
            ),
            RenderedEntry(
                headword="beta",
                html="<b>synthetic beta</b>",
            ),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stats = write_stardict(entries, root, "Synthetic")

            self.assertEqual(stats.wordcount, 2)
            self.assertEqual(stats.synwordcount, 1)
            self.assertTrue((root / "Synthetic.dict").is_file())
            self.assertTrue((root / "Synthetic.idx").is_file())
            self.assertTrue((root / "Synthetic.ifo").is_file())
            self.assertTrue((root / "Synthetic.syn").is_file())
            self.assertTrue((root / "Synthetic.css").is_file())

            syn = (root / "Synthetic.syn").read_bytes()
            word, raw_index = syn.split(b"\x00", 1)
            self.assertEqual(word, b"alphas")
            self.assertEqual(struct.unpack(">I", raw_index)[0], 0)


if __name__ == "__main__":
    unittest.main()
