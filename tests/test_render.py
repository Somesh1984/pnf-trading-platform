from __future__ import annotations

import unittest

from pnf.render import columns_to_rows, columns_to_table, render_ascii_chart
from tests.helpers import make_column


class RenderTests(unittest.TestCase):
    def test_columns_to_table_is_read_only(self) -> None:
        columns = [make_column("X", "100", "102", 0, count=3)]
        before = columns[0]
        table = columns_to_table(columns)
        self.assertEqual(table[0]["type"], "X")
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
