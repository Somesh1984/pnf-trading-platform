from __future__ import annotations

from csv import DictReader
from pathlib import Path
from typing import Any

import numpy as np

from chart_pnf import PointFigureChart
from chart_pnf.chart_shared import SIGNAL_TYPES, tabulate

DEMO_LAST_ROWS = 750
DEMO_PRINT_COLUMNS = 20
DEMO_PRINT_ASCII = False
DEMO_PRINT_PATTERNS = True
DEMO_SHOW_PLOT = True

CHART_SIGNAL_TYPES = {
    0: "Buy Signal",
    1: "Sell Signal",
    2: "Double Top Breakout",
    3: "Double Bottom Breakdown",
    4: "Triple Top Breakout",
    5: "Triple Bottom Breakdown",
    6: "Quadruple Top Breakout",
    7: "Quadruple Bottom Breakdown",
    9: "Ascending Triple Top Breakout",
    10: "Descending Triple Bottom Breakdown",
    11: "Bullish Catapult Breakout",
    12: "Bearish Catapult Breakdown",
    13: "Bullish Signal Reversed",
    14: "Bullish Triangle Breakout",
    15: "Bearish Triangle Breakdown",
    18: "Bull Trap",
    19: "Spread Triple Top Breakout",
    20: "Spread Triple Bottom Breakdown",
    22: "High Pole",
    23: "Low Pole",
}


def load_demo_data() -> dict[str, list[Any]]:
    data: dict[str, list[Any]] = {
        "date": [],
        "open": [],
        "high": [],
        "low": [],
        "close": [],
    }
    data_path = Path(__file__).with_name("data") / "nifty.csv"
    with data_path.open(newline="") as handle:
        rows = list(DictReader(handle))

    if DEMO_LAST_ROWS is not None:
        rows = rows[-DEMO_LAST_ROWS:]

    for row in rows:
        data["date"].append(row["time"])
        data["open"].append(float(row["open"]))
        data["high"].append(float(row["high"]))
        data["low"].append(float(row["low"]))
        data["close"].append(float(row["close"]))

    return data


def format_demo_value(value: Any) -> str:
    if isinstance(value, np.datetime64):
        return np.datetime_as_string(value, unit="s").replace("T", " ")

    return str(value)


def pattern_name(pattern_index: int) -> str:
    if pattern_index in CHART_SIGNAL_TYPES:
        return CHART_SIGNAL_TYPES[pattern_index]

    if 0 <= pattern_index < len(SIGNAL_TYPES):
        return SIGNAL_TYPES[pattern_index]

    return f"Pattern Type {pattern_index}"


def print_patterns(pnf: PointFigureChart) -> None:
    signals = pnf.get_signals()
    rows: list[list[Any]] = [["column", "date", "pattern", "price", "width"]]

    for column_index, width in enumerate(signals["width"]):
        if width == 0:
            continue

        box_index = signals["box index"][column_index]
        ts_index = signals["ts index"][column_index]
        pattern_index = int(signals["type"][column_index])
        price = pnf.boxscale[box_index]
        date = pnf.pnf_timeseries["date"][ts_index]

        rows.append(
            [
                column_index,
                format_demo_value(date),
                pattern_name(pattern_index),
                price,
                width,
            ]
        )

    print(tabulate(rows, tablefmt="simple"))
    print(f"patterns: {len(rows) - 1}")


def main() -> None:
    pnf = PointFigureChart(
        ts=load_demo_data(),
        method="h/l",
        reversal=3,
        boxsize=0.25,
        scaling="log",
        title="NIFTY",
    )
    pnf.print_columns = DEMO_PRINT_COLUMNS

    if DEMO_PRINT_ASCII:
        print(pnf)

    if DEMO_PRINT_PATTERNS:
        print_patterns(pnf)

    if DEMO_SHOW_PLOT:
        pnf.get_trendlines(length=4, mode="weak")
        pnf.show_trendlines = "external"
        pnf.get_breakouts()
        pnf.show_breakouts = True
        # pnf.bollinger(5, 2)
        # pnf.donchian(8, 2)
        # pnf.psar(0.02, 0.2)
        pnf.show()


if __name__ == "__main__":
    main()
