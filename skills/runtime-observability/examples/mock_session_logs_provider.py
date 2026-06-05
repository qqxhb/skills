#!/usr/bin/env python3
"""Mock session_logs provider for local verification."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit a mock raw session log payload")
    parser.add_argument("--session-id", required=True, help="Session id placeholder")
    args = parser.parse_args()

    _ = args.session_id
    sample = Path(__file__).resolve().parent / "sample-session-log.json"
    print(sample.read_text(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
