# Daily Market Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a two-layer daily market report system: Python scripts fetch structured market data as JSON, a Claude Code skill reads that JSON and writes an AI-analyzed Markdown report to `wiki/market/`.

**Architecture:** Python layer (`scripts/market/`) handles deterministic data fetching (yfinance + scraping) and outputs JSON to stdout. Claude Code skill (`market-daily.md`) orchestrates the fetch, analyzes the data, and writes the final Markdown report. No separate API key required.

**Tech Stack:** Python 3.11+, yfinance, requests, beautifulsoup4, Claude Code skills

---

## File Map

| Action | Path | Purpose |
|--------|------|---------|
| Create | `scripts/market/__init__.py` | Python package marker |
| Create | `scripts/market/yfinance_data.py` | Fetch index/sector/watchlist prices via yfinance |
| Create | `scripts/market/news_scraper.py` | Scrape Finviz headlines |
| Create | `scripts/market/sentiment.py` | Fetch CNN Fear & Greed score |
| Create | `scripts/gen_daily_market.py` | CLI entrypoint — aggregates all data, prints JSON |
| Create | `.claude/skills/market-daily.md` | Skill — runs script, analyzes JSON, writes report |
| Modify | `requirements-dev.txt` | Add yfinance, requests, beautifulsoup4 |
| Create | `tests/market/test_yfinance_data.py` | Unit tests for price fetching |
| Create | `tests/market/test_news_scraper.py` | Unit tests for news scraping |
| Create | `tests/market/test_sentiment.py` | Unit tests for sentiment fetching |
| Create | `tests/market/test_gen_daily_market.py` | Integration tests for JSON output |

---

## Task 1: Add dependencies

**Files:**
- Modify: `requirements-dev.txt`

- [ ] **Step 1: Add new dependencies**

Edit `requirements-dev.txt` to:

```
python-frontmatter==1.1.0
pyyaml==6.0.2
pytest==8.3.4
yfinance>=0.2.50
requests>=2.31
beautifulsoup4>=4.12
```

- [ ] **Step 2: Install dependencies**

```bash
pip install yfinance requests beautifulsoup4
```

Expected: All three packages install without error.

- [ ] **Step 3: Verify install**

```bash
python -c "import yfinance; import requests; import bs4; print('OK')"
```

Expected output: `OK`

- [ ] **Step 4: Commit**

```bash
git add requirements-dev.txt
git commit -m "chore: add yfinance, requests, beautifulsoup4 dependencies"
```

---

## Task 2: `yfinance_data.py` — price and volume data

**Files:**
- Create: `scripts/market/__init__.py`
- Create: `scripts/market/yfinance_data.py`
- Create: `tests/market/__init__.py`
- Create: `tests/market/test_yfinance_data.py`

- [ ] **Step 1: Write failing tests**

Create `tests/market/__init__.py` (empty).

Create `tests/market/test_yfinance_data.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/market/test_yfinance_data.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `scripts.market.yfinance_data` does not exist yet.

- [ ] **Step 3: Create package marker**

Create `scripts/market/__init__.py` (empty file).

- [ ] **Step 4: Implement `yfinance_data.py`**

Create `scripts/market/yfinance_data.py`:

```python
from __future__ import annotations
from dataclasses import dataclass, field
import sys
import yfinance as yf

INDICES = ["SPY", "QQQ", "^DJI"]

SECTORS = {
    "XLK": "科技", "XLE": "能源", "XLF": "金融", "XLV": "医疗",
    "XLI": "工业", "XLB": "材料", "XLU": "公用事业",
    "XLRE": "房地产", "XLP": "必需消费", "XLY": "可选消费",
}


@dataclass
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
        change = close - prev
        pct = round(change / prev * 100, 2)
        vol_ratio = round(vol / avg_vol, 2)
        return StockQuote(ticker=ticker, close=close, change=round(change, 2), pct=pct, vol_ratio=vol_ratio)
    except Exception as e:
        print(f"WARN: failed to fetch {ticker}: {e}", file=sys.stderr)
        return None


def fetch_quotes(tickers: list[str]) -> list[StockQuote]:
    results = []
    for t in tickers:
        q = fetch_quote(t)
        if q:
            results.append(q)
    return results


def fetch_snapshot(
    index_tickers: list[str],
    sector_tickers: list[str],
    watchlist_tickers: list[str],
) -> MarketSnapshot:
    snap = MarketSnapshot()
    for t in index_tickers:
        q = fetch_quote(t)
        if q:
            snap.indices.append(q)
    snap.sectors = fetch_quotes(sector_tickers)
    snap.watchlist = fetch_quotes(watchlist_tickers)
    return snap
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/market/test_yfinance_data.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/market/__init__.py scripts/market/yfinance_data.py tests/market/__init__.py tests/market/test_yfinance_data.py
git commit -m "feat: add yfinance_data module with StockQuote and MarketSnapshot"
```

---

## Task 3: `news_scraper.py` — Finviz headlines

**Files:**
- Create: `scripts/market/news_scraper.py`
- Create: `tests/market/test_news_scraper.py`

- [ ] **Step 1: Write failing tests**

Create `tests/market/test_news_scraper.py`:

```python
from __future__ import annotations
import pytest
from unittest.mock import patch, MagicMock
from scripts.market.news_scraper import fetch_news, NewsItem

SAMPLE_HTML = """
<html><body>
<table class="fullview-news-outer">
  <tr><td>
    <span class="date">Apr-25-26</span>
    <a href="https://example.com/story1">Fed holds rates steady</a>
  </td></tr>
  <tr><td>
    <span class="date">Apr-25-26</span>
    <a href="https://example.com/story2">Nvidia leads chip rally</a>
  </td></tr>
</table>
</body></html>
"""


def test_fetch_news_parses_headlines():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = SAMPLE_HTML
    with patch("scripts.market.news_scraper.requests.get", return_value=mock_resp):
        items = fetch_news(max_items=5)
    assert len(items) == 2
    assert items[0].title == "Fed holds rates steady"
    assert items[0].url == "https://example.com/story1"


def test_fetch_news_returns_empty_on_error():
    with patch("scripts.market.news_scraper.requests.get", side_effect=Exception("timeout")):
        items = fetch_news(max_items=5)
    assert items == []


def test_fetch_news_respects_max_items():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = SAMPLE_HTML
    with patch("scripts.market.news_scraper.requests.get", return_value=mock_resp):
        items = fetch_news(max_items=1)
    assert len(items) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/market/test_news_scraper.py -v
```

Expected: `ImportError` — module does not exist yet.

- [ ] **Step 3: Implement `news_scraper.py`**

Create `scripts/market/news_scraper.py`:

```python
from __future__ import annotations
from dataclasses import dataclass
import sys
import requests
from bs4 import BeautifulSoup

FINVIZ_URL = "https://finviz.com/news.ashx"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; market-daily/1.0)"}


@dataclass
class NewsItem:
    title: str
    url: str


def fetch_news(max_items: int = 5) -> list[NewsItem]:
    try:
        resp = requests.get(FINVIZ_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []
        for a in soup.select("table.fullview-news-outer a[href]"):
            title = a.get_text(strip=True)
            url = a["href"]
            if title and url.startswith("http"):
                items.append(NewsItem(title=title, url=url))
            if len(items) >= max_items:
                break
        return items
    except Exception as e:
        print(f"WARN: news fetch failed: {e}", file=sys.stderr)
        return []
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/market/test_news_scraper.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/market/news_scraper.py tests/market/test_news_scraper.py
git commit -m "feat: add news_scraper module for Finviz headlines"
```

---

## Task 4: `sentiment.py` — CNN Fear & Greed

**Files:**
- Create: `scripts/market/sentiment.py`
- Create: `tests/market/test_sentiment.py`

- [ ] **Step 1: Write failing tests**

Create `tests/market/test_sentiment.py`:

```python
from __future__ import annotations
from unittest.mock import patch, MagicMock
from scripts.market.sentiment import fetch_sentiment, SentimentResult

SAMPLE_JSON = {
    "fear_and_greed": {
        "score": 42.0,
        "rating": "Fear",
        "previous_close": 47.0,
    }
}


def test_fetch_sentiment_parses_score():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_JSON
    with patch("scripts.market.sentiment.requests.get", return_value=mock_resp):
        result = fetch_sentiment()
    assert result is not None
    assert result.score == 42
    assert result.label == "Fear"
    assert result.prev_score == 47


def test_fetch_sentiment_returns_none_on_error():
    with patch("scripts.market.sentiment.requests.get", side_effect=Exception("timeout")):
        result = fetch_sentiment()
    assert result is None


def test_fetch_sentiment_returns_none_on_missing_key():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"unexpected": "data"}
    with patch("scripts.market.sentiment.requests.get", return_value=mock_resp):
        result = fetch_sentiment()
    assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/market/test_sentiment.py -v
```

Expected: `ImportError` — module does not exist yet.

- [ ] **Step 3: Implement `sentiment.py`**

Create `scripts/market/sentiment.py`:

```python
from __future__ import annotations
from dataclasses import dataclass
import sys
import requests

CNN_API_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; market-daily/1.0)"}


@dataclass
class SentimentResult:
    score: int
    label: str
    prev_score: int


def fetch_sentiment() -> SentimentResult | None:
    try:
        resp = requests.get(CNN_API_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        fg = data["fear_and_greed"]
        return SentimentResult(
            score=int(fg["score"]),
            label=fg["rating"],
            prev_score=int(fg["previous_close"]),
        )
    except Exception as e:
        print(f"WARN: sentiment fetch failed: {e}", file=sys.stderr)
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/market/test_sentiment.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/market/sentiment.py tests/market/test_sentiment.py
git commit -m "feat: add sentiment module for CNN Fear and Greed index"
```

---

## Task 5: `gen_daily_market.py` — JSON aggregator CLI

**Files:**
- Create: `scripts/gen_daily_market.py`
- Create: `tests/market/test_gen_daily_market.py`

- [ ] **Step 1: Write failing tests**

Create `tests/market/test_gen_daily_market.py`:

```python
from __future__ import annotations
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from scripts.market.yfinance_data import StockQuote, MarketSnapshot
from scripts.market.news_scraper import NewsItem
from scripts.market.sentiment import SentimentResult

# Add scripts/ to path so gen_daily_market can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/market/test_gen_daily_market.py -v
```

Expected: `ImportError` or `ModuleNotFoundError`.

- [ ] **Step 3: Implement `gen_daily_market.py`**

Create `scripts/gen_daily_market.py`:

```python
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

    # Enrich sector names
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
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/market/test_gen_daily_market.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Smoke test (requires network)**

```bash
python scripts/gen_daily_market.py | python -m json.tool | head -40
```

Expected: Valid JSON with `date`, `indices`, `sectors`, `watchlist`, `sentiment`, `news` keys. Some values may be `null` if a data source is unavailable.

- [ ] **Step 6: Commit**

```bash
git add scripts/gen_daily_market.py tests/market/test_gen_daily_market.py
git commit -m "feat: add gen_daily_market CLI that outputs structured market JSON"
```

---

## Task 6: Run all tests

**Files:** (no new files)

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/market/ -v
```

Expected: All tests PASS. Count should be 10 tests total across 4 files.

- [ ] **Step 2: If any test fails, fix before proceeding**

Do not proceed to Task 7 until all tests pass.

---

## Task 7: Create the `market-daily` skill

**Files:**
- Create: `.claude/skills/market-daily.md`

- [ ] **Step 1: Create `.claude/skills/` directory if it doesn't exist**

```bash
mkdir -p .claude/skills
```

- [ ] **Step 2: Create skill file**

Create `.claude/skills/market-daily.md`:

````markdown
# market-daily

Generate today's market report: fetch live data, analyze it, and write to `wiki/market/`.

## Arguments

Optional: `--date YYYY-MM-DD` to generate a report for a past date.

## Steps

### 1. Determine report date

If `--date` was passed as an argument, use that date. Otherwise use today's date in `YYYY-MM-DD` format.

### 2. Fetch market data

Run the Python fetch script. Capture stdout as JSON.

```bash
python scripts/gen_daily_market.py --date <DATE>
```

If the script exits non-zero or produces no output, stop and report the error. Do not write a partial report.

### 3. Check for existing report

Check if `wiki/market/<DATE>.md` already exists. If it does, ask the user whether to overwrite before proceeding.

### 4. Analyze the data

Read the JSON output carefully. Write the analysis with these three sections:

**市场概况 (Market Overview):**
- What happened to the major indices today? Up or down, by how much?
- Connect the move to the news headlines. What macro event, earnings, or Fed signal explains the direction?
- Keep to 2-3 sentences.

**板块轮动 (Sector Rotation):**
- Which sectors led and which lagged?
- Is the pattern risk-on (tech/growth leading) or risk-off (utilities/staples leading)?
- Any notable divergence between sectors?
- Keep to 2-3 sentences.

**Watchlist 亮点 (Watchlist Highlights):**
- Which watchlist tickers moved significantly (>2% or vol_ratio >1.5x)?
- For each notable mover, 1 sentence: what moved it and whether it aligns with the thesis.
- If no watchlist tickers moved significantly, say so briefly.

### 5. Write the report

Write `wiki/market/<DATE>.md` with this exact structure:

```markdown
# 市场日报 · <DATE>

*由 `/market-daily` skill 自动生成。*

## 市场情绪
Fear & Greed: <score> (<label>) <direction_arrow> 昨日 <prev>

(If sentiment data unavailable: `（数据不可用）`)

## 主要指数
| 指数 | 收盘 | 涨跌 | 涨跌幅 |
|------|------|------|--------|
(one row per index; use N/A if data missing)

## 板块表现
**涨幅前三：** <name> <pct>% · <name> <pct>% · <name> <pct>%
**跌幅前三：** <name> <pct>% · <name> <pct>% · <name> <pct>%

## Watchlist 个股
| Ticker | 收盘 | 涨跌幅 | 量比 |
|--------|------|--------|------|
(one row per ticker; sort by abs(pct) descending)

## 今日要闻
(bullet list of news items; if empty: `（今日新闻获取失败）`)
- [<title>](<url>) — Finviz

## AI 解读

**市场概况：** <2-3 sentences>

**板块轮动：** <2-3 sentences>

**Watchlist 亮点：** <highlights or "今日 watchlist 无显著异动">
```

Direction arrow rules: if `score > prev`, use `↑`; if `score < prev`, use `↓`; if equal, omit arrow.

### 6. Update the index

Read `wiki/market/index.md` (create it if missing). Keep only the most recent 30 entries. The index format:

```markdown
# 市场日报归档

*Auto-generated by `/market-daily`. Do not edit by hand.*

| 日期 | 情绪 | SPY | QQQ |
|------|------|-----|-----|
| [2026-04-25](2026-04-25.md) | 42 Fear | -0.81% | +0.35% |
```

Add the new date at the top. Remove entries beyond 30.

### 7. Confirm completion

Report: "市场日报已生成：`wiki/market/<DATE>.md`"
````

- [ ] **Step 3: Verify skill is discoverable**

```bash
ls .claude/skills/market-daily.md
```

Expected: file exists.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/market-daily.md
git commit -m "feat: add market-daily skill for AI-analyzed daily market report"
```

---

## Task 8: Create `wiki/market/` directory

**Files:**
- Create: `wiki/market/.gitkeep`

- [ ] **Step 1: Create directory and placeholder**

```bash
mkdir -p wiki/market
touch wiki/market/.gitkeep
```

- [ ] **Step 2: Commit**

```bash
git add wiki/market/.gitkeep
git commit -m "chore: add wiki/market/ directory for daily market reports"
```

---

## Task 9: End-to-end test

**Files:** (no new files)

- [ ] **Step 1: Run the skill**

In Claude Code, invoke:

```
/market-daily
```

- [ ] **Step 2: Verify output file exists**

```bash
ls wiki/market/
```

Expected: a file named `<today's date>.md` exists.

- [ ] **Step 3: Verify file contents**

```bash
cat wiki/market/<today>.md
```

Expected:
- All 6 sections present (情绪, 指数, 板块, Watchlist, 要闻, AI解读)
- No empty `AI 解读` section
- Markdown table syntax is valid (no broken pipes)

- [ ] **Step 4: Verify index**

```bash
cat wiki/market/index.md
```

Expected: index file exists with one entry for today.

- [ ] **Step 5: Commit generated files (optional)**

If you want to keep the first report in git:

```bash
git add wiki/market/
git commit -m "feat: add first daily market report"
```

---

## Done ✓

The feature is complete when:
- `pytest tests/market/ -v` → all green
- `/market-daily` runs end-to-end and writes a complete report with AI analysis
- `wiki/market/index.md` is created and updated

**Next step:** Once you've run it a few times manually and the output looks good, use `/schedule` to set up daily automation.
