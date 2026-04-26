#!/usr/bin/env python3
"""Fetch daily market data and output as JSON to stdout.

Usage:
  python scripts/gen_daily_market.py
  python scripts/gen_daily_market.py --date 2026-04-24
  python scripts/gen_daily_market.py --wiki-root ../stock-kb/wiki
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from market.yfinance_data import fetch_snapshot, INDICES, SECTORS
from market.news_scraper import fetch_news
from market.sentiment import fetch_sentiment

DEFAULT_WIKI = SCRIPT_DIR.parent / "wiki"


def discover_watchlist(tickers_dir: Path) -> list[str]:
    if not tickers_dir.is_dir():
        return []
    return sorted(
        d.name for d in tickers_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )


def build_payload(report_date: str, tickers_dir: Path) -> dict:
    watchlist = discover_watchlist(tickers_dir)
    snapshot = fetch_snapshot(INDICES, list(SECTORS.keys()), watchlist)
    news = fetch_news(max_items=5)
    sentiment = fetch_sentiment()

    def quote_to_dict(q):
        return {"ticker": q.ticker, "close": q.close, "change": q.change, "pct": q.pct, "vol_ratio": q.vol_ratio}

    sector_dicts = []
    for q in snapshot.sectors:
        d = quote_to_dict(q)
        d["name"] = SECTORS.get(q.ticker, q.ticker)
        sector_dicts.append(d)

    return {
        "date": report_date,
        "indices": [quote_to_dict(q) for q in snapshot.indices],
        "sectors": sector_dicts,
        "watchlist": [quote_to_dict(q) for q in snapshot.watchlist],
        "sentiment": {"score": sentiment.score, "label": sentiment.label, "prev": sentiment.prev_score} if sentiment else None,
        "news": [{"title": n.title, "url": n.url} for n in news],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", default=str(date.today()), help="Report date (YYYY-MM-DD)")
    ap.add_argument("--wiki-root", type=Path, default=DEFAULT_WIKI)
    args = ap.parse_args()

    tickers_dir = args.wiki_root / "tickers"
    payload = build_payload(args.date, tickers_dir)
    sys.stdout.reconfigure(encoding="utf-8")
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
