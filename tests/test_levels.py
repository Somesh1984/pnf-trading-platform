from __future__ import annotations

import unittest

from pnf.core import PnFConfig
from pnf.levels import detect_horizontal_levels
from tests.helpers import make_column


class LevelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = PnFConfig(box_pct=0.01, reversal=3)

    def test_detects_horizontal_resistance_and_support_with_minimum_touches(self) -> None:
        columns = [
            make_column("X", "100", "103", 0),
            make_column("O", "99", "102", 1),
            make_column("X", "101", "103", 2),
            make_column("O", "99", "102", 3),
            make_column("X", "100", "103", 4),
            make_column("O", "99", "102", 5),
        ]
        levels = detect_horizontal_levels(columns, self.config)
        self.assertEqual({level.kind for level in levels}, {"resistance", "support"})
        self.assertTrue(all(level.touches == 3 for level in levels))

    def test_cluster_threshold_is_in_box_units(self) -> None:
        columns = [
            make_column("X", "100", "103", 0),
            make_column("X", "100", "104", 1),
            make_column("X", "100", "103", 2),
        ]
        self.assertEqual(detect_horizontal_levels(columns, self.config, cluster_threshold_boxes=0), [])
        levels = detect_horizontal_levels(columns, self.config, cluster_threshold_boxes=1)
        self.assertEqual(len(levels), 1)
        self.assertEqual(levels[0].touches, 3)

    def test_levels_reject_weak_configuration(self) -> None:
        with self.assertRaises(ValueError):
            detect_horizontal_levels([make_column("X", "100", "103", 0)], self.config, min_touches=2)
