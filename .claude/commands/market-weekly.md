# market-weekly

Generate the weekly market report: review this week's performance, track potential stock follow-through, and preview next week's key events. Writes to `wiki/market/`.

## Arguments

Optional: `--week YYYY-WXX` to generate a report for a specific ISO week (e.g. `--week 2026-W18`). Otherwise uses the current week.

## Steps

### 1. Determine report week

If `--week` was passed, use that value. Otherwise compute the current ISO week:

```bash
python -c "import datetime; today = datetime.date.today(); y, w, _ = today.isocalendar(); print(f'{y}-W{w:02d}')"
```

Also compute Monday and Friday dates for this week:

```bash
python -c "import datetime; today = datetime.date.today(); mon = today - datetime.timedelta(days=today.weekday()); fri = mon + datetime.timedelta(days=4); print(mon.strftime('%Y-%m-%d'), fri.strftime('%Y-%m-%d'))"
```

Store: `WEEK_ID` (e.g. `2026-W18`), `WEEK_MON`, `WEEK_FRI`.

Output filename: `wiki/market/weekly-<WEEK_ID>.md`

### 2. Check for existing report

Check if `wiki/market/weekly-<WEEK_ID>.md` already exists. If so, ask the user whether to overwrite before proceeding.

### 3. Read this week's daily reports

List all files in `wiki/market/` matching dates `<WEEK_MON>` through `<WEEK_FRI>` (excluding `weekly-*`, `monthly-*`, `quarterly-*`, and `index.md`). Read each daily report that exists.

Extract and aggregate:
- Fear & Greed scores (list per day)
- Index performance per day (SPY, QQQ, DIA pct change)
- Notable AI interpretation highlights per day (key sentences from each day's 市场概况 and 板块轮动)
- Watchlist tickers with significant daily moves
- Any tickers that appeared in 今日潜力股候选 sections — collect all, note the day and their score (X/4)

Note how many of the 5 trading days have reports.

### 4. Fetch weekly index and watchlist performance

Use the `yfinance-data` skill to get weekly returns (Monday open to Friday close) for:
- SPY, QQQ, DIA, IWM (Russell 2000), VIX

For each watchlist ticker (tickers with files in `wiki/tickers/`): weekly return, weekly volume trend.

### 5. Fetch sector weekly performance

Use the `yfinance-data` skill to get weekly returns for major sector ETFs:
XLK, XLF, XLV, XLE, XLI, XLU, XLP, XLY, XLRE, XLB, XLC

Sort by weekly return. Note top 3 (领涨) and bottom 3 (领跌).

### 6. Get next week's economic calendar

Export from the unusual_whales Telegram bot:

```bash
tdl chat export -c 5241900942 -T last -i 10 --all --with-content -o ~/tdl-exports/uw_weekly.json
```

Look in `~/tdl-exports/uw_weekly.json` for `/economic_calendar` messages. Extract event name, date, expected impact, and consensus estimate where available.

If not found in the export, note: "下周经济日历：请手动查阅 unusual_whales `/economic_calendar`。"

### 7. Get next week's earnings schedule

In `~/tdl-exports/uw_weekly.json`, look for `/earnings_premarket` and `/earnings_afterhours` messages for next week's dates. Extract tickers and dates.

Also use the `yfinance-data` skill to check if any watchlist tickers have earnings scheduled next week. Note each ticker's date, time (pre/post market), and current consensus EPS.

### 8. Track potential stock follow-through

For each ticker collected in Step 3 from 今日潜力股候选 sections, use `yfinance-data` to get its performance from the day it appeared to Friday close. Compare vs SPY weekly return for the same window. Classify: Hit (positive alpha vs SPY) / Miss (underperformed SPY or negative) / Too soon (appeared late in the week, insufficient window).

### 9. Analyze and write AI commentary

Write these sections:

**本周回顾 (Week in Review):**
- What were the dominant market themes this week?
- How did macro events (Fed speakers, economic data, earnings) affect markets?
- What drove sector leadership and lagging?
- Keep to 3-4 sentences.

**Watchlist 周表现 (Watchlist Weekly):**
- For each watchlist ticker with a notable weekly move (>5% or significant news): 1 sentence on what drove it and thesis alignment.
- If no notable movers, note overall watchlist direction vs benchmark.

**潜力股追踪 (Potential Stock Follow-Through):**
- How did this week's 今日潜力股候选 tickers perform?
- Any patterns: which dimension combinations (T+S, T+O, etc.) correlated with better follow-through?
- If no candidates appeared this week, note it.

**下周展望 (Next Week Outlook):**
- Key macro events from the economic calendar and what to watch for
- Watchlist tickers with upcoming earnings and what to monitor
- Overall market technical setup and sentiment going into next week
- Keep to 3-4 sentences.

### 10. Write the weekly report

Write `wiki/market/weekly-<WEEK_ID>.md`:

```markdown
# 市场周报 · <WEEK_ID>（<WEEK_MON> — <WEEK_FRI>）

*由 `/market-weekly` 自动生成。*

## 本周市场情绪
Fear & Greed — 周均：<avg> | 区间：<min>–<max>
总体情绪：[偏多 / 中性 / 偏空]

## 主要指数周表现
| 指数 | 周涨跌幅 | 周收盘 |
|------|---------|--------|
| SPY | +X.XX% | $XXX.XX |
| QQQ | +X.XX% | $XXX.XX |
| DIA | +X.XX% | $XXX.XX |
| IWM | +X.XX% | $XXX.XX |
| VIX | +X.XX% | XX.XX |

## 板块周表现
**领涨：** [Top 3 sectors with weekly pct]
**领跌：** [Bottom 3 sectors with weekly pct]

## Watchlist 周表现
| Ticker | 周涨跌幅 | 周收盘 | 论文对齐 |
|--------|---------|--------|---------|
（论文对齐：✅ 符合 / ⚠️ 部分 / ❌ 背离 / — 无显著变化）

## 潜力股候选追踪
（本周日报中出现的 今日潜力股候选 的后续表现）

| Ticker | 出现日期 | 评分 | 本周表现 | vs SPY | 结果 |
|--------|---------|------|---------|--------|------|
（本周无潜力股候选 → 写：本周日报无潜力股候选记录）

## AI 解读

**本周回顾：** <3-4 sentences>

**Watchlist 周表现：** <highlights>

**潜力股追踪：** <follow-through summary or "本周无候选记录">

**下周展望：** <3-4 sentences>

## 下周日历

### 重要经济数据
（数据不可用则写：请手动查阅 unusual_whales `/economic_calendar`）

| 日期 | 事件 | 预期影响 | 共识 |
|------|------|---------|------|

### 财报提示

| Ticker | 日期 | 时间 | 共识 EPS |
|--------|------|------|---------|
（Watchlist 优先；下周无 watchlist 财报 → 写：下周 watchlist 无财报）
```

### 11. Confirm completion

Report: "市场周报已生成：`wiki/market/weekly-<WEEK_ID>.md`"
