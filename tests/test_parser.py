# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic parser tests."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from houaiss3_stardict.parser import parse_entries  # noqa: E402


SYNTHETIC = """\
Synthetic format header ignored by the parser
*lexeme-alpha
n1
d2001
B0
C01|n.|synthetic noun
A0
-1
:a fictional definition created only for testing
<an invented example|another invented example
TSYN|synthetic field
Plexeme-alphas
$lexeme_alpha
3invented origin
*lexeme-beta
C02|v.|synthetic verb
-1
:another fictional definition
"""


class ParserTests(unittest.TestCase):
    def test_entries_and_aliases(self) -> None:
        entries = list(parse_entries(SYNTHETIC.splitlines()))
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].headword, "lexeme-alpha")
        self.assertEqual(entries[0].homonym, "1")
        self.assertIn("lexeme-alphas", entries[0].aliases)
        self.assertIn("lexeme_alpha", entries[0].aliases)


if __name__ == "__main__":
    unittest.main()
