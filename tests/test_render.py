from __future__ import annotations

from decimal import Decimal
import unittest

from pnf.render import columns_to_rows, columns_to_table, render_ascii_chart
from tests.helpers import make_column


class RenderTests(unittest.TestCase):
    def test_empty_columns_render_empty_ascii_chart(self) -> None:
        self.assertEqual(render_ascii_chart([]), "")
        self.assertEqual(columns_to_rows([]), [])
        self.assertEqual(columns_to_table([]), [])

    def test_columns_to_table_is_read_only(self) -> None:
        columns = [make_column("X", "100", "102", 0, count=3)]
        before = columns[0]

        table = columns_to_table(columns)

        self.assertEqual(set(table[0]), {"type", "box_count", "high", "low", "start_index", "end_index"})
        self.assertEqual(table[0]["type"], "X")
        self.assertEqual(table[0]["box_count"], 3)
        self.assertEqual(table[0]["high"], Decimal("102"))
        self.assertEqual(table[0]["low"], Decimal("100"))
        self.assertEqual(table[0]["start_index"], 0)
        self.assertEqual(table[0]["end_index"], 0)
        self.assertEqual(columns[0], before)

    def test_columns_to_rows_and_ascii_chart(self) -> None:
        columns = [
            make_column("X", "100", "102", 0, count=3),
            make_column("O", "99", "101", 1, count=3),
        ]
        rows = columns_to_rows(columns)
        chart = render_ascii_chart(columns)
        self.assertEqual(rows[0]["price"], columns[0].high)
        self.assertIn("X", chart)
        self.assertIn("O", chart)

    def test_ascii_chart_has_exact_readable_output(self) -> None:
        columns = [
            make_column("X", "100", "102", 0, count=3),
            make_column("O", "99", "101", 1, count=3),
        ]

        chart = render_ascii_chart(columns)

        self.assertEqual(
            chart,
            "\n".join(
                [
                    "    0 1",
                    "102 X .",
                    "101 X O",
                    "100 X O",
                    " 99 . O",
                ]
            ),
        )

    def test_rendering_is_deterministic_and_read_only(self) -> None:
        columns = [
            make_column("X", "100", "102", 0, count=3),
            make_column("O", "99", "101", 1, count=3),
        ]
        before = tuple(columns)

        first = render_ascii_chart(columns)
        second = render_ascii_chart(columns)

        self.assertEqual(first, second)
        self.assertEqual(tuple(columns), before)
