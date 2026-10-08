# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic tests for inline markup conversion."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from houaiss3_stardict.markup import inline_to_html  # noqa: E402


class MarkupTests(unittest.TestCase):
    def test_italic_and_bold_groups(self) -> None:
        value = r"plain {\i invented} and {\b synthetic}"
        rendered = inline_to_html(value)
        self.assertIn("<i>invented</i>", rendered)
        self.assertIn("<b>synthetic</b>", rendered)

    def test_plain_text_is_escaped(self) -> None:
        self.assertEqual(inline_to_html("a < b & c"), "a &lt; b &amp; c")


if __name__ == "__main__":
    unittest.main()
