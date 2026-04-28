#!/usr/bin/env python3
"""Read and filter UW bot Telegram export JSON, with proper UTF-8 handling.

Usage:
  py scripts/read_uw_bot.py --path ~/tdl-exports/uw_daily.json --ticker POET
  py scripts/read_uw_bot.py --path ~/tdl-exports/uw_daily.json --section flow
  py scripts/read_uw_bot.py --path ~/tdl-exports/uw_daily.json --section screen
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys

# Force UTF-8 output regardless of Windows console codepage
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


FLOW_KEYWORDS = {"sweep", "flow", "unusual", "call", "put", "bullish", "bearish", "alert"}
DARK_KEYWORDS = {"dark", "darkpool", "off-exchange", "print", "block"}
SCREEN_KEYWORDS = {"trading_above_average", "52_week_high", "hottest_chains"}


def clean(text: str) -> str:
    """Replace non-printable chars; keep basic ASCII + common punctuation."""
    return text.encode("utf-8", errors="replace").decode("utf-8")


def load_messages(path: str) -> list[dict]:
    expanded = os.path.expanduser(path)
    try:
        with open(expanded, encoding="utf-8", errors="replace") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[read_uw_bot] File not found: {expanded}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"[read_uw_bot] JSON parse error: {e}", file=sys.stderr)
        return []
    if isinstance(data, dict):
        return data.get("messages", [])
    if isinstance(data, list):
        return data
    return []


def get_text(msg: dict) -> str:
    return msg.get("text") or msg.get("message") or ""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", required=True, help="Path to UW bot JSON export")
    ap.add_argument("--ticker", help="Filter messages containing this ticker symbol")
    ap.add_argument(
        "--section",
        choices=["flow", "darkpool", "screen", "all"],
        default="all",
        help="Which message category to output",
    )
    ap.add_argument("--limit", type=int, default=10, help="Max messages to print")
    args = ap.parse_args()

    messages = load_messages(args.path)
    if not messages:
        print("无数据")
        return

    results: list[str] = []
    for msg in messages:
        text = get_text(msg)
        if not text:
            continue

        text_lower = text.lower()

        # Ticker filter
        if args.ticker and args.ticker.upper() not in text.upper():
            continue

        # Section filter
        if args.section == "flow":
            if not any(kw in text_lower for kw in FLOW_KEYWORDS):
                continue
        elif args.section == "darkpool":
            if not any(kw in text_lower for kw in DARK_KEYWORDS):
                continue
        elif args.section == "screen":
            if not any(kw in text_lower for kw in SCREEN_KEYWORDS):
                continue

        results.append(clean(text[:300]))

    if not results:
        print("无匹配数据")
        return

    for r in results[-args.limit:]:
        print(r)
        print("---")


if __name__ == "__main__":
    main()
