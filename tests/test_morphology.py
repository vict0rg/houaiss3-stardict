# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic tests for auxiliary lookup mapping and optional morphology."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from houaiss3_stardict.indexdata import (  # noqa: E402
    parse_detailed_index,
    parse_group_index,
)
from houaiss3_stardict.morphology import (  # noqa: E402
    build_conservative_nominal_aliases,
    parse_auxiliary_aliases,
)


class MorphologyTests(unittest.TestCase):
    def test_zero_based_detailed_reference_is_accepted(self) -> None:
        detailed = parse_detailed_index(
            "alpha;1;0;p;\n"
            "target;2;0;p;\n"
            "omega;3;0;p;\n"
        )
        grouped = parse_group_index(
            "alpha;1;0;p;\n"
            "target;2;0;p;\n"
            "omega;3;0;p;\n"
        )

        mapping, stats = parse_auxiliary_aliases(
            "surface;1;2;p;\n",
            detailed,
            grouped,
        )

        self.assertEqual(mapping["target"], {"surface"})
        self.assertEqual(stats["p1_zero_only"], 1)
        self.assertEqual(stats["crosscheck_mismatch"], 0)

    def test_one_based_detailed_reference_is_accepted(self) -> None:
        detailed = parse_detailed_index(
            "alpha;1;0;p;\n"
            "target;2;0;p;\n"
            "omega;3;0;p;\n"
        )
        grouped = parse_group_index(
            "alpha;1;0;p;\n"
            "target;2;0;p;\n"
            "omega;3;0;p;\n"
        )

        mapping, stats = parse_auxiliary_aliases(
            "surface;2;2;p;\n",
            detailed,
            grouped,
        )

        self.assertEqual(mapping["target"], {"surface"})
        self.assertEqual(stats["p1_one_only"], 1)
        self.assertEqual(stats["crosscheck_mismatch"], 0)

    def test_detailed_reference_must_validate_group_target(self) -> None:
        detailed = parse_detailed_index(
            "alpha;1;0;p;\n"
            "beta;2;0;p;\n"
            "gamma;3;0;p;\n"
        )
        grouped = parse_group_index(
            "alpha;1;0;p;\n"
            "target;2;0;p;\n"
            "gamma;3;0;p;\n"
        )

        mapping, stats = parse_auxiliary_aliases(
            "surface;1;2;p;\n",
            detailed,
            grouped,
        )

        self.assertEqual(mapping, {})
        self.assertEqual(stats["crosscheck_mismatch"], 1)

    def test_conservative_nominal_mapping_is_optional_and_unambiguous(self) -> None:
        mapping, stats = build_conservative_nominal_aliases(
            ["systems", "women", "radars"],
            {"system", "radar"},
        )

        self.assertEqual(mapping["system"], {"systems"})
        self.assertEqual(mapping["radar"], {"radars"})
        self.assertGreaterEqual(stats["no_candidate"], 1)

class NominalFallbackPrecedenceTests(unittest.TestCase):
    def test_source_occupied_alias_is_not_reinferred(self) -> None:
        mapping, stats = build_conservative_nominal_aliases(
            ["systems"],
            {"system"},
            occupied_aliases={"systems"},
        )

        self.assertEqual(mapping, {})
        self.assertEqual(stats["already_mapped"], 1)

if __name__ == "__main__":
    unittest.main()
