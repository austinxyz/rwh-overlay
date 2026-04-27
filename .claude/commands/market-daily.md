# market-daily

Generate today's market report: fetch live data, analyze with social sentiment and options flow signals, and write to `wiki/market/`.

## Arguments

Optional: `--date YYYY-MM-DD` to generate a report for a past date.

## Steps

### 1. Determine report date

If `--date` was passed as an argument, use that date. Otherwise use today's date in `YYYY-MM-DD` format.

Determine if the date is a **weekend** (Saturday or Sunday). This controls which report format to use.

### 2. Fetch market data

Run the Python fetch script. Capture stdout as JSON.

```bash
py scripts/gen_daily_market.py --date <DATE>
```

If the script exits non-zero or produces no output, stop and report the error. Do not write a partial report.

### 3. Check for existing report

Check if `wiki/market/<DATE>.md` already exists. If it does, ask the user whether to overwrite before proceeding.

### 4. Fetch social sentiment (weekday only)

Skip this step on weekends.

Use the `finance-sentiment` skill to get **overall market** social sentiment:
- Reddit market sentiment (r/wallstreetbets, r/stocks, r/investing) — overall bullish/bearish signal today
- X.com market sentiment — key trending financial topics
- News sentiment for major indices (S&P 500, Nasdaq)
- Overall signal: Bullish / Neutral / Bearish

Also run `finance-sentiment` for any watchlist tickers that had notable moves (>2% or vol_ratio >1.5x from Step 2 data).

### 5. Query options flow and darkpool signals (weekday only)

Skip this step on weekends.

Export recent messages from the unusual_whales Telegram bot:

```bash
tdl chat export -c 5241900942 -T last -i 10 --all --with-content -o ~/tdl-exports/uw_daily.json
```

Read `~/tdl-exports/uw_daily.json` and extract:

**Options flow signals:**
- Messages containing flow alerts or unusual sweeps (large call or put sweeps)
- For each signal: ticker, direction (看涨 call / 看跌 put), premium size if stated

**Darkpool signals:**
- Large off-exchange prints
- For each: ticker and size

If the export is unavailable or contains no relevant data, note "期权流/暗池数据不可用" and continue.

### 6. Screen for potential stocks (weekday only)

Skip this step on weekends.

In `~/tdl-exports/uw_daily.json` (from Step 5), look for messages from: `/trading_above_average`, `/52_week_high`, `/hottest_chains_bullish`. Extract ticker lists.

If these messages are absent from the recent export, write "本日无潜力股筛选数据" in the 今日潜力股候选 section and skip the rest of this step.

When ticker lists are available, take up to 10 unique tickers (deduplicated, highest mention frequency first). For each candidate, evaluate four dimensions:

| 维度 | 工具 | 通过标准 |
|------|------|---------|
| 技术（T）| `sepa-strategy` | Stage 2，趋势模板 ≥5/8，量能配合 |
| 情绪（S）| `finance-sentiment` | 综合情绪偏多，讨论量中以上 |
| 期权流（O）| Step 5 数据 | 异常看涨成交量或大宗 call sweep |
| 基本面（F）| `estimate-analysis` | 近 90 日分析师预期上调 |

Include only tickers with ≥3/4 dimensions passing. If none qualify, write "本日无符合四维标准的候选。"

### 7. Analyze the data

**If it is a weekday**, write the AI analysis with these sections:

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

**市场异常信号 (Anomaly Signals):**
- Summarize key options flow and darkpool findings from Steps 5–6.
- If no signals, write "本日无显著异常信号".
- Keep to 2-3 sentences.

**社交情绪 (Social Sentiment):**
- Overall market social sentiment from Step 4.
- Any notable shift in retail sentiment vs the prior reading.
- Keep to 1-2 sentences.

**If it is a weekend**, write the analysis with one section:

**周末要闻解读 (Weekend News Commentary):**
- Summarize the key themes across the news headlines.
- What macro risks or opportunities do these stories suggest for the coming week?
- Keep to 3-4 sentences.

### 8. Write the report

**If it is a weekday**, write `wiki/market/<DATE>.md` with this exact structure:

```markdown
# 市场日报 · <DATE>

*由 `/market-daily` 自动生成。*

## 市场情绪
Fear & Greed: <score> (<label>) <direction_arrow> 昨日 <prev>

*0-24 极度恐慌 · 25-44 恐慌 · 45-55 中性 · 56-74 贪婪 · 75-100 极度贪婪*

（如数据不可用：`（数据不可用）`）

## 主要指数
| 指数 | 收盘 | 涨跌 | 涨跌幅 |
|------|------|------|--------|
（每个指数一行；数据缺失用 N/A）

## 板块表现
**涨幅前三：** <name> <pct>% · <name> <pct>% · <name> <pct>%
**跌幅前三：** <name> <pct>% · <name> <pct>% · <name> <pct>%

## Watchlist 个股
| Ticker | 收盘 | 涨跌幅 | 量比 |
|--------|------|--------|------|
（每个 ticker 一行；按 abs(pct) 降序排列）

## 市场异常信号

### 期权流
（来自 unusual_whales Telegram bot；一条一行）
（无信号：本日无显著期权流信号）

### 暗池大单
（来自 unusual_whales Telegram bot；一条一行）
（无信号：本日无显著暗池大单）

## 今日要闻
（新闻为空时写：`（今日新闻获取失败）`）
- [<title>](<url>) — Finviz

## AI 解读

**市场概况：** <2-3 sentences>

**板块轮动：** <2-3 sentences>

**Watchlist 亮点：** <highlights 或 "今日 watchlist 无显著异动">

**市场异常信号：** <summary 或 "本日无显著异常信号">

**社交情绪：** <1-2 sentences>

## 今日潜力股候选
（四维筛选：技术 + 情绪 + 期权流 + 基本面，至少 3/4 维正向）

（本日无符合条件的候选 或 本日无潜力股筛选数据 → 写对应说明）

| Ticker | 技术 | 情绪 | 期权流 | 基本面 | 总分 |
|--------|------|------|--------|--------|------|
（✅ 通过 · ⚠️ 部分 · ❌ 不符）

**简评：**
（每只候选一行：TICKER：[1-2 句信号来源]）
```

**If it is a weekend**, write `wiki/market/<DATE>.md` with this structure instead:

```markdown
# 市场日报 · <DATE>（非交易日）

*由 `/market-daily` 自动生成。周末无行情数据，仅展示要闻与情绪。*

## 市场情绪
Fear & Greed: <score> (<label>) <direction_arrow> 昨日 <prev>

*0-24 极度恐慌 · 25-44 恐慌 · 45-55 中性 · 56-74 贪婪 · 75-100 极度贪婪*

（如数据不可用：`（数据不可用）`）

## 周末要闻
（新闻为空时写：`（今日新闻获取失败）`）
- [<title>](<url>) — Finviz

## AI 解读

**周末要闻解读：** <3-4 sentences summarizing themes and implications for next week>
```

Direction arrow rules: if `score > prev`, use `↑`; if `score < prev`, use `↓`; if equal, omit arrow.

### 9. Update the index

Read `wiki/market/index.md` (create it if missing). Keep only the most recent 30 entries. The index format:

```markdown
# 市场日报归档

*Auto-generated by `/market-daily`. Do not edit by hand.*

*情绪指引：0-24 极度恐慌 · 25-44 恐慌 · 45-55 中性 · 56-74 贪婪 · 75-100 极度贪婪*

| 日期 | 情绪 | SPY | QQQ | 道指 | 领涨 | 领跌 | 最大异动 |
|------|------|-----|-----|------|------|------|----------|
| [2026-04-25](2026-04-25.md) | 66 Greed | +0.77% | +1.91% | -0.16% | 科技+2.8% | 医疗-1.4% | POET+28.8% |
```

Column rules:
- **领涨 / 领跌**: top and bottom sector by pct, format `<name><pct>%` (e.g. `科技+2.8%`)
- **最大异动**: watchlist ticker with largest abs(pct), format `<TICKER><pct>%` (e.g. `POET+28.8%`)
- For weekend entries, use `—` in SPY, QQQ, 道指, 领涨, 领跌, 最大异动 columns

Add the new date at the top. Remove entries beyond 30.

### 10. Confirm completion

Report: "市场日报已生成：`wiki/market/<DATE>.md`"
