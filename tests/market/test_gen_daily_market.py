from __future__ import annotations
import json
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from scripts.market.yfinance_data import StockQuote, MarketSnapshot
from scripts.market.news_scraper import NewsItem
from scripts.market.sentiment import SentimentResult
import gen_daily_market as gdm


def _mock_snapshot():
    return MarketSnapshot(
        indices=[StockQuote("SPY", 512.3, -4.2, -0.81, 1.0)],
        sectors=[StockQuote("XLK", 200.0, -2.0, -1.0, 0.9)],
        watchlist=[StockQuote("NVTS", 3.21, 0.13, 4.2, 1.8)],
    )


def test_build_payload_structure():
    with patch("gen_daily_market.fetch_snapshot", return_value=_mock_snapshot()), \
         patch("gen_daily_market.fetch_news", return_value=[NewsItem("Headline", "http://x.com")]), \
         patch("gen_daily_market.fetch_sentiment", return_value=SentimentResult(42, "Fear", 47)):
        payload = gdm.build_payload("2026-04-25", Path("wiki/tickers"))

    assert payload["date"] == "2026-04-25"
    assert len(payload["indices"]) == 1
    assert payload["indices"][0]["ticker"] == "SPY"
    assert len(payload["sectors"]) == 1
    assert payload["sectors"][0]["name"] == "科技"   # XLK → 科技
    assert len(payload["watchlist"]) == 1
    assert payload["watchlist"][0]["vol_ratio"] == 1.8
    assert payload["sentiment"]["score"] == 42
    assert len(payload["news"]) == 1


def test_build_payload_null_sentiment():
    with patch("gen_daily_market.fetch_snapshot", return_value=_mock_snapshot()), \
         patch("gen_daily_market.fetch_news", return_value=[]), \
         patch("gen_daily_market.fetch_sentiment", return_value=None):
        payload = gdm.build_payload("2026-04-25", Path("wiki/tickers"))

    assert payload["sentiment"] is None
    assert payload["news"] == []


def test_discover_watchlist_tickers(tmp_path):
    (tmp_path / "NVTS").mkdir()
    (tmp_path / "OKLO").mkdir()
    (tmp_path / ".gitkeep").touch()
    tickers = gdm.discover_watchlist(tmp_path)
    assert set(tickers) == {"NVTS", "OKLO"}
