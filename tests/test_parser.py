# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic parser tests."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from houaiss3_stardict.parser import parse_entries  # noqa: E402


SYNTHETIC = """\
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
r01|tr.|synthetic transitive
LSYN|lang.|synthetic language
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

    def test_three_part_metadata_is_split_cleanly(self) -> None:
        entries = list(parse_entries(SYNTHETIC.splitlines()))
        regency = next(
            block for block in entries[0].blocks if block.label == "Regência"
        )
        language = next(
            block for block in entries[0].blocks if block.label == "Língua"
        )
        self.assertEqual(regency.abbreviation, "tr.")
        self.assertEqual(regency.text, "synthetic transitive")
        self.assertEqual(language.abbreviation, "lang.")
        self.assertEqual(language.text, "synthetic language")


if __name__ == "__main__":
    unittest.main()
