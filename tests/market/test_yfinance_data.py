from __future__ import annotations
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from scripts.market.yfinance_data import (
    fetch_quote,
    fetch_quotes,
    StockQuote,
    MarketSnapshot,
    fetch_snapshot,
)


def _mock_ticker(close: float, prev_close: float, volume: int, avg_volume: int) -> MagicMock:
    info = {
        "regularMarketPrice": close,
        "regularMarketPreviousClose": prev_close,
        "regularMarketVolume": volume,
        "averageVolume": avg_volume,
    }
    t = MagicMock()
    t.info = info
    return t


def test_fetch_quote_calculates_change_and_pct():
    with patch("scripts.market.yfinance_data.yf.Ticker") as mock_cls:
        mock_cls.return_value = _mock_ticker(
            close=100.0, prev_close=98.0, volume=1_000_000, avg_volume=500_000
        )
        quote = fetch_quote("SPY")
    assert quote.ticker == "SPY"
    assert abs(quote.change - 2.0) < 0.01
    assert abs(quote.pct - 2.04) < 0.01
    assert abs(quote.vol_ratio - 2.0) < 0.01


def test_fetch_quote_returns_none_on_error():
    with patch("scripts.market.yfinance_data.yf.Ticker") as mock_cls:
        mock_cls.side_effect = Exception("network error")
        quote = fetch_quote("BAD")
    assert quote is None


def test_fetch_quotes_skips_failed():
    def side_effect(ticker):
        if ticker == "GOOD":
            return _mock_ticker(10.0, 9.0, 100, 50)
        raise Exception("fail")

    with patch("scripts.market.yfinance_data.yf.Ticker", side_effect=side_effect):
        quotes = fetch_quotes(["GOOD", "BAD"])
    assert len(quotes) == 1
    assert quotes[0].ticker == "GOOD"


def test_market_snapshot_has_expected_fields():
    with patch("scripts.market.yfinance_data.fetch_quote") as mock_fq:
        mock_fq.return_value = StockQuote(
            ticker="SPY", close=512.3, change=-4.2, pct=-0.81, vol_ratio=1.0
        )
        with patch("scripts.market.yfinance_data.fetch_quotes") as mock_fqs:
            mock_fqs.return_value = [
                StockQuote(ticker="XLK", close=200.0, change=-2.0, pct=-1.0, vol_ratio=0.9)
            ]
            snap = fetch_snapshot(["SPY", "QQQ", "^DJI"], ["XLK"], ["NVTS"])
    assert isinstance(snap, MarketSnapshot)
    assert len(snap.indices) > 0
    assert len(snap.sectors) > 0
    assert len(snap.watchlist) > 0
