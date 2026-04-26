from __future__ import annotations
from dataclasses import dataclass, field
import logging
import sys
import yfinance as yf

logger = logging.getLogger(__name__)

INDICES = ["SPY", "QQQ", "^DJI"]

SECTORS = {
    "XLK": "科技", "XLE": "能源", "XLF": "金融", "XLV": "医疗",
    "XLI": "工业", "XLB": "材料", "XLU": "公用事业",
    "XLRE": "房地产", "XLP": "必需消费", "XLY": "可选消费",
}


@dataclass(frozen=True)
class StockQuote:
    ticker: str
    close: float
    change: float
    pct: float
    vol_ratio: float


@dataclass
class MarketSnapshot:
    indices: list[StockQuote] = field(default_factory=list)
    sectors: list[StockQuote] = field(default_factory=list)
    watchlist: list[StockQuote] = field(default_factory=list)


def fetch_quote(ticker: str) -> StockQuote | None:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        close = float(info["regularMarketPrice"])
        prev = float(info["regularMarketPreviousClose"])
        vol = int(info.get("regularMarketVolume", 0))
        avg_vol = int(info.get("averageVolume", 1)) or 1
        if not prev:
            logger.warning(f"zero prev_close for {ticker}")
            return None
        change = close - prev
        pct = round(change / prev * 100, 2)
        vol_ratio = round(vol / avg_vol, 2)
        return StockQuote(ticker=ticker, close=close, change=round(change, 2), pct=pct, vol_ratio=vol_ratio)
    except Exception as e:
        logger.warning(f"failed to fetch {ticker}: {e}")
        return None


def fetch_quotes(tickers: list[str]) -> list[StockQuote]:
    results = []
    for ticker in tickers:
        q = fetch_quote(ticker)
        if q:
            results.append(q)
    return results


def fetch_snapshot(
    index_tickers: list[str],
    sector_tickers: list[str],
    watchlist_tickers: list[str],
) -> MarketSnapshot:
    indices = [q for t in index_tickers if (q := fetch_quote(t))]
    return MarketSnapshot(
        indices=indices,
        sectors=fetch_quotes(sector_tickers),
        watchlist=fetch_quotes(watchlist_tickers),
    )
