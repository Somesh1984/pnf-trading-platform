from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path[0] = str(Path(__file__).resolve().parents[1])

from trading_app.config import load_config, redacted_config
from trading_app.health import check_questdb_health
from trading_app.logging import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trading_app")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("show-config", help="Print redacted runtime config")
    subparsers.add_parser("health", help="Check QuestDB HTTP health")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config()
    configure_logging(config.log_level)

    if args.command == "show-config":
        print(json.dumps(redacted_config(config), indent=2, sort_keys=True))
        return 0

    if args.command == "health":
        result = check_questdb_health(config)
        status = "ok" if result.ok else "failed"
        print(f"questdb {status}: {result.detail} ({result.url})")
        return 0 if result.ok else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
