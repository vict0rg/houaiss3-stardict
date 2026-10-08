# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic renderer tests."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from houaiss3_stardict.model import Block, Entry  # noqa: E402
from houaiss3_stardict.renderer import render_entry  # noqa: E402


class RendererTests(unittest.TestCase):
    def test_dictionary_labels_are_portuguese(self) -> None:
        entry = Entry(
            headword="synthetic",
            blocks=[
                Block(kind="date", text="2001"),
                Block(kind="metadata", label="Rubrica", text="synthetic field"),
                Block(
                    kind="metadata",
                    label="Regência",
                    text="synthetic transitive",
                    abbreviation="tr.",
                ),
                Block(kind="metadata", label="Tradução", text="synthetic translation"),
                Block(kind="registered_trademark"),
                Block(kind="etymology", text="synthetic origin"),
            ],
        )
        html = render_entry(entry)
        self.assertIn("Datação:", html)
        self.assertIn("Rubrica:", html)
        self.assertIn("Regência:", html)
        self.assertIn("Tradução:", html)
        self.assertIn("Marca registrada", html)
        self.assertIn("Etimologia:", html)
        self.assertIn("tr.</span> — synthetic transitive", html)

    def test_subentry_alternative_separators_are_rendered_neutrally(self) -> None:
        entry = Entry(
            headword="synthetic",
            blocks=[
                Block(
                    kind="subentry",
                    text="first form# second form @ third form",
                )
            ],
        )

        html = render_entry(entry)

        self.assertIn("first form / second form / third form", html)
        self.assertNotIn("# second", html)
        self.assertNotIn("@ third", html)


if __name__ == "__main__":
    unittest.main()
