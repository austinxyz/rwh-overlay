# Daily Market Report Design

**Date**: 2026-04-25  
**Owner**: austinxyz  
**Status**: Approved (v2 — Skill + Python hybrid)

---

## 1. Problem Statement

The user wants a daily automated market analysis stored as Markdown files in the existing `wiki/` structure and optionally pushed as a notification. The report should cover major US indices, sector performance, watchlist individual stocks, market sentiment, and AI-generated interpretation of the data — all without requiring a separate Claude API key.

## 2. Goals

- **G1** Generate one Markdown file per trading day under `wiki/market/YYYY-MM-DD.md`.
- **G2** Auto-discover watchlist tickers from existing `wiki/tickers/` directory.
- **G3** Cover: major indices (SPY/QQQ/DJI), 10 SPDR sector ETFs, watchlist per-stock, Fear & Greed sentiment, top news headlines.
- **G4** Any single data source failure degrades gracefully — the report is always written.
- **G5** AI analysis (Claude) interprets the data: key drivers, sector rotation, watchlist highlights.
- **G6** No separate API key required — runs within Claude Code subscription via Skill.
- **G7** Manually triggered at first; `/schedule` automation added once stable.

## 3. Non-Goals

- **NG1** No standalone scheduling at launch — script + skill first, `/schedule` later.
- **NG2** No LLM commentary on individual stock fundamentals — daily price/volume context only.
- **NG3** No historical backfill automation — `--date` flag supports manual one-offs.
- **NG4** No modification to `build_stock_kb.py` — daily market runs independently.
- **NG5** No separate Claude API billing — analysis runs inside Claude Code session only.

## 4. Architecture

### 4.1 Two-Layer Design

```
Layer 1 — Data Collection (Python, deterministic, testable)
  scripts/gen_daily_market.py      ← CLI entrypoint, outputs JSON to stdout
  scripts/market/
    __init__.py
    yfinance_data.py               ← price/volume via yfinance
    news_scraper.py                ← headlines via requests + BeautifulSoup
    sentiment.py                   ← Fear & Greed via CNN API

Layer 2 — Analysis + Report Writing (Claude Code Skill)
  .claude/skills/market-daily.md   ← skill: orchestrates fetch → analyze → write
```

### 4.2 Execution Flow

```
User invokes /market-daily
  ↓
Skill: run python scripts/gen_daily_market.py [--date YYYY-MM-DD]
  ↓
Python outputs JSON to stdout:
  {
    "date": "2026-04-25",
    "indices": [{"ticker": "SPY", "close": 512.3, "change": -4.2, "pct": -0.81}, ...],
    "sectors": [{"name": "能源", "etf": "XLE", "pct": 1.2}, ...],
    "watchlist": [{"ticker": "NVTS", "close": 3.21, "pct": 4.2, "vol_ratio": 1.8}, ...],
    "sentiment": {"score": 42, "label": "Fear", "prev": 47},
    "news": [{"title": "...", "url": "..."}]
  }
  ↓
Claude reads JSON → analyzes data
  - Identifies key index drivers
  - Explains sector rotation signals
  - Highlights watchlist movers
  - Contextualizes news impact
  ↓
Claude writes wiki/market/YYYY-MM-DD.md
Claude updates wiki/market/index.md
```

### 4.3 Module Responsibilities

| Component | Responsibility | Does NOT |
|-----------|---------------|----------|
| `yfinance_data.py` | Fetch price, volume, 20-day avg vol | Write files or interpret |
| `news_scraper.py` | Scrape Finviz headlines + URLs | Rank or filter |
| `sentiment.py` | Fetch CNN Fear & Greed score | Interpret direction |
| `gen_daily_market.py` | Aggregate all data, output JSON to stdout | Write Markdown |
| `market-daily.md` (skill) | Run script, analyze JSON, write Markdown | Fetch data directly |

### 4.4 Data Sources

| Data | Source | Method |
|------|--------|--------|
| Index prices (SPY, QQQ, ^DJI) | Yahoo Finance | `yfinance` library |
| Sector ETF prices (XLK, XLE, XLF, XLV, XLI, XLB, XLU, XLRE, XLP, XLY) | Yahoo Finance | `yfinance` library |
| Watchlist individual stocks | Yahoo Finance | `yfinance` library |
| Volume ratio (vol / 20-day avg) | Yahoo Finance | `yfinance` library |
| News headlines (top 5) | Finviz front page | `requests` + `BeautifulSoup` |
| Fear & Greed index | CNN Fear & Greed API | `requests` (JSON) |

Watchlist tickers are auto-discovered by listing `wiki/tickers/` subdirectories.

## 5. Output Format

```markdown
# 市场日报 · 2026-04-25

*由 `/market-daily` skill 自动生成。*

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

## 今日要闻
- [Fed holds rates steady amid inflation uncertainty](url) — Finviz
- [Nvidia leads chip stocks higher on AI demand](url) — Finviz

## AI 解读

**市场概况：** [Claude 对当日整体市场走势的简短分析，结合要闻解释指数涨跌原因]

**板块轮动：** [Claude 解读板块强弱，是否有明显的避险/风险偏好信号]

**Watchlist 亮点：** [Claude 点评当日 watchlist 中表现突出或异常的个股，结合量比]
```

## 6. Error Handling

Each Python data source fails independently:

- `yfinance_data.py` failure → affected cells show `N/A` in JSON; skill renders `N/A` in table
- `news_scraper.py` failure → `"news": []` in JSON; skill renders `（今日新闻获取失败）`
- `sentiment.py` failure → `"sentiment": null` in JSON; skill renders `（数据不可用）`

Python script always exits with code 0 and always emits valid JSON (with null fields on partial failure).

If the Python script fails entirely, the skill catches the error, reports it, and does not write a partial file.

## 7. CLI Interface (Python layer)

```bash
# Output today's data as JSON to stdout
python scripts/gen_daily_market.py

# Output data for a specific date (backfill)
python scripts/gen_daily_market.py --date 2026-04-24
```

The skill handles `--date` forwarding and file writing. No `--force` flag needed (skill controls overwrite behavior).

## 8. Skill Interface

Skill file: `.claude/skills/market-daily.md`

Invocation: `/market-daily` (optionally `/market-daily --date 2026-04-24`)

The skill:
1. Runs the Python fetch script
2. Reads JSON output
3. Analyzes with Claude
4. Writes `wiki/market/YYYY-MM-DD.md`
5. Updates `wiki/market/index.md` (last 30 days)

## 9. New Dependencies

Add to `requirements-dev.txt`:

```
yfinance>=0.2.50
requests>=2.31
beautifulsoup4>=4.12
```

## 10. Integration with Existing Pipeline

`gen_daily_market.py` is standalone. `wiki/market/` is picked up by Syncthing to NAS and served by Quartz — no changes needed to `build_stock_kb.py` or Quartz config.
