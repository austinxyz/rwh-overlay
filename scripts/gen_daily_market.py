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

# Import market submodules using their absolute path to avoid collision with any
# `market` package that a test runner may have registered from a test directory.
import importlib.util as _ilu

def _load_market_module(name: str):
    """Load scripts/market/<name>.py by path, bypassing sys.modules['market']."""
    src = SCRIPT_DIR / "market" / f"{name}.py"
    spec = _ilu.spec_from_file_location(f"market.{name}", src)
    mod = _ilu.module_from_spec(spec)
    sys.modules[f"market.{name}"] = mod
    spec.loader.exec_module(mod)
    return mod

_yfinance_data = _load_market_module("yfinance_data")
fetch_snapshot = _yfinance_data.fetch_snapshot
INDICES = _yfinance_data.INDICES
SECTORS = _yfinance_data.SECTORS

_news_scraper = _load_market_module("news_scraper")
fetch_news = _news_scraper.fetch_news

_sentiment = _load_market_module("sentiment")
fetch_sentiment = _sentiment.fetch_sentiment

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
    # Reconfigure stdout to UTF-8 to handle Chinese sector names on Windows.
    out = sys.stdout.buffer if hasattr(sys.stdout, "buffer") else sys.stdout
    import io
    writer = io.TextIOWrapper(out, encoding="utf-8") if hasattr(sys.stdout, "buffer") else sys.stdout
    json.dump(payload, writer, ensure_ascii=False, indent=2)
    writer.write("\n")
    writer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
