# Daily Market Report Design

**Date**: 2026-04-25  
**Owner**: austinxyz  
**Status**: Approved

---

## 1. Problem Statement

The user wants a daily automated market analysis stored as Markdown files in the existing `wiki/` structure and optionally pushed as a notification. The report should cover major US indices, sector performance, watchlist individual stocks, and market sentiment — scraped from external sources and published to the Quartz wiki via the existing sync pipeline.

## 2. Goals

- **G1** Generate one Markdown file per trading day under `wiki/market/YYYY-MM-DD.md`.
- **G2** Auto-discover watchlist tickers from existing `wiki/tickers/` directory.
- **G3** Cover: major indices (SPY/QQQ/DJI), 10 SPDR sector ETFs, watchlist per-stock, Fear & Greed sentiment, top news headlines.
- **G4** Any single data source failure degrades gracefully — the report is always written.
- **G5** Optional webhook notification (Slack / WeCom compatible) via env var, zero code changes to enable.
- **G6** Follows existing `scripts/gen_*.py` single-entrypoint pattern.

## 3. Non-Goals

- **NG1** No scheduling — script only; cron/Task Scheduler setup is out of scope for this spec.
- **NG2** No LLM-generated analysis or commentary — raw data only.
- **NG3** No historical backfill automation — `--date` flag supports manual one-offs.
- **NG4** No modification to `build_stock_kb.py` — daily market runs independently.

## 4. Architecture

### 4.1 File Layout

```
scripts/
  gen_daily_market.py          # entrypoint: orchestrates fetch + render
  market/
    __init__.py                # empty
    yfinance_data.py           # price/volume data via yfinance
    news_scraper.py            # news headlines via requests + BeautifulSoup
    sentiment.py               # Fear & Greed index via CNN API

wiki/
  market/
    YYYY-MM-DD.md              # one file per trading day (permanent archive)
    index.md                   # auto-generated index of recent 30 days
```

### 4.2 Data Flow

```
gen_daily_market.py
  ├── yfinance_data.py  → MarketSnapshot (indices, sectors, watchlist stocks)
  ├── news_scraper.py   → list[NewsItem]
  ├── sentiment.py      → SentimentResult
  └── render_markdown() → wiki/market/YYYY-MM-DD.md
  └── update_index()    → wiki/market/index.md
```

### 4.3 Module Responsibilities

| Module | Input | Output | Does NOT |
|--------|-------|--------|----------|
| `yfinance_data.py` | ticker list, date | `MarketSnapshot` dataclass | write files |
| `news_scraper.py` | (fixed Finviz URL) | `list[NewsItem]` | filter or rank |
| `sentiment.py` | (fixed CNN API URL) | `SentimentResult` | interpret direction |
| `gen_daily_market.py` | outputs of above | Markdown files | fetch data directly |

### 4.4 Data Sources

| Data | Source | Method |
|------|--------|--------|
| Index prices (SPY, QQQ, DJI) | Yahoo Finance | `yfinance` library |
| Sector ETF prices (XLK, XLE, XLF, XLV, XLI, XLB, XLU, XLRE, XLP, XLY) | Yahoo Finance | `yfinance` library |
| Watchlist individual stocks | Yahoo Finance | `yfinance` library |
| Volume ratio (vol / 20-day avg) | Yahoo Finance | `yfinance` library |
| News headlines (top 5) | Finviz front page | `requests` + `BeautifulSoup` |
| Fear & Greed index | CNN Fear & Greed API | `requests` (JSON response) |

Watchlist tickers are auto-discovered by listing `wiki/tickers/` subdirectories — no separate config file needed.

## 5. Output Format

```markdown
# 市场日报 · YYYY-MM-DD

## 市场情绪
Fear & Greed: 42 (Fear) ↓ 昨日 47

## 主要指数
| 指数 | 收盘 | 涨跌 | 涨跌幅 |
|------|------|------|--------|
| SPY  | 512.3 | -4.2 | -0.81% |
| QQQ  | 430.1 | +1.5 | +0.35% |
| DJI  | 38,200 | -120 | -0.31% |

## 板块表现
**涨幅前三：** 能源 +1.2% · 材料 +0.8% · 工业 +0.5%
**跌幅前三：** 科技 -1.1% · 通信 -0.7% · 金融 -0.4%

## Watchlist 个股
| Ticker | 收盘 | 涨跌幅 | 量比 |
|--------|------|--------|------|
| NVTS   | 3.21 | +4.2%  | 1.8x |

## 今日要闻（驱动因素）
- [Headline text](url) — Finviz
```

## 6. Error Handling

Each data source fails independently with graceful degradation:

- `yfinance_data.py` failure → affected table cells show `N/A`; report still written
- `news_scraper.py` failure → news section shows `（今日新闻获取失败）`
- `sentiment.py` failure → sentiment line shows `（数据不可用）`

All errors print to stderr. Script always exits with code 0 to ensure the file is always generated (important for downstream sync pipeline).

## 7. CLI Interface

```bash
# Generate today's report
python scripts/gen_daily_market.py

# Generate report for a specific date (backfill)
python scripts/gen_daily_market.py --date 2026-04-24

# Overwrite existing file
python scripts/gen_daily_market.py --force
```

## 8. Optional Notification

After writing the Markdown file, the script checks for `NOTIFY_WEBHOOK` environment variable:

- **Set** → POST a brief summary (index performance + F&G value) as JSON to the URL. Compatible with Slack incoming webhooks and WeCom (企业微信) bot webhooks.
- **Not set** → silently skipped, no error.

This allows enabling notifications at scheduling time via env var without any code changes.

## 9. New Dependencies

Add to `requirements-dev.txt`:

```
yfinance>=0.2.50
requests>=2.31
beautifulsoup4>=4.12
```

## 10. Integration with Existing Pipeline

`gen_daily_market.py` is a standalone script. It writes to `wiki/market/` which is picked up by the existing Syncthing sync to NAS and served by Quartz — no changes needed to `build_stock_kb.py` or the Quartz config.
