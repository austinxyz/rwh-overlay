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

### 4. Fetch social sentiment (always)

Use the `finance-sentiment` skill to get **overall market** social sentiment:
- Reddit market sentiment (r/wallstreetbets, r/stocks, r/investing) — overall bullish/bearish signal today
- X.com market sentiment — key trending financial topics
- News sentiment for major indices (S&P 500, Nasdaq)
- Overall signal: Bullish / Neutral / Bearish

On weekdays only: also run `finance-sentiment` for any watchlist tickers that had notable moves (>2% or vol_ratio >1.5x from Step 2 data). Skip per-ticker sentiment on weekends (no fresh market move to anchor it).

### 5. Query options flow and darkpool signals (weekday only)

Skip this step on weekends.

Export recent messages from the unusual_whales Telegram bot, then use the helper script to parse:

```bash
tdl chat export -c 5241900942 -T last -i 10 --all --with-content -o ~/tdl-exports/uw_daily.json
py scripts/read_uw_bot.py --path ~/tdl-exports/uw_daily.json --section flow --limit 10
py scripts/read_uw_bot.py --path ~/tdl-exports/uw_daily.json --section darkpool --limit 5
```

Extract from helper output:

**Options flow signals:**
- Messages containing flow alerts or unusual sweeps (large call or put sweeps)
- For each signal: ticker, direction (看涨 call / 看跌 put), premium size if stated

**Darkpool signals:**
- Large off-exchange prints
- For each: ticker and size

If the export is unavailable or the helper returns "无数据", note "期权流/暗池数据不可用" and continue.

### 6. Screen for potential stocks (weekday only)

Skip this step on weekends.

**Step 6a — Build the candidate pool (two sources, merge and deduplicate):**

Source 1 — UW scanner messages (if available):
```bash
py scripts/read_uw_bot.py --path ~/tdl-exports/uw_daily.json --section screen --limit 5
```
Extract tickers from `/trading_above_average`, `/52_week_high`, `/hottest_chains_bullish` messages.

Source 2 — Watchlist notable movers from Step 2 data (always available):
Use any watchlist ticker with abs(pct) >2% OR vol_ratio >1.5x as a candidate.

Merge both sources, deduplicate, take up to 10 tickers (UW tickers first, then watchlist movers).

**If both sources yield zero candidates**, write "本日无潜力股候选（指数平静，watchlist 无显著异动）" and skip the rest of this step.

**Step 6b — Evaluate each candidate on four dimensions:**

| 维度 | 工具 | 通过标准 | 无数据时 |
|------|------|---------|---------|
| 技术（T）| `sepa-strategy` | Stage 2，趋势模板 ≥5/8，量能配合 | ❌ 不符 |
| 情绪（S）| `finance-sentiment` | 综合情绪偏多，讨论量中以上 | ⚠️ N/A |
| 期权流（O）| Step 5 UW 数据 | 异常看涨成交量或大宗 call sweep | ⚠️ N/A（UW 无数据时跳过，不计入分母）|
| 基本面（F）| `estimate-analysis` | 近 90 日分析师预期上调 | ⚠️ N/A |

**入选规则：**
- 当 O 维度有数据时：≥3/4 维度通过方可入选
- 当 O 维度 N/A 时：≥2/3 可评估维度通过即入选（T+S、T+F 或 S+F 任意两项）
- 无论 O 是否可用，T（技术）必须通过（Stage 2）才纳入候选

If none qualify, write "本日无符合标准的候选。"

### 7. Analyze the data

**If it is a weekday**, write the AI analysis with these sections, each using bullet points (not prose paragraphs):

**市场概况 (Market Overview):**
- One bullet: indices direction + magnitude
- One bullet: macro driver connecting the move to news/earnings/Fed
- e.g. "SPY +0.8%，QQQ +1.9%：科技财报超预期带动纳指领涨"

**板块轮动 (Sector Rotation):**
- One bullet: top sectors with pct
- One bullet: lagging sectors with pct
- One bullet: risk-on / risk-off 判断 + 有无明显异常

**Watchlist 亮点 (Watchlist Highlights):**
- One bullet per notable mover (>2% or vol_ratio >1.5x): TICKER±X% — 原因 — 是否符合论点
- If none: "今日 watchlist 无显著异动"

**市场异常信号 (Anomaly Signals):**
- One bullet per notable options flow or darkpool signal
- If none: "本日无显著异常信号"

**社交情绪 (Social Sentiment):**
- One bullet per platform with notable reading
- One bullet: overall signal vs. prior day / F&G alignment

**If it is a weekend**, write the analysis with two sections, each using bullet points (not prose paragraphs):

**周末要闻解读 (Weekend News Commentary):**
- One bullet per key news theme (2-4 bullets)
- Each bullet: theme → implication for next week
- e.g. "伊朗和谈停滞 → 油价溢价可能持续，XLE 值得关注"

**社交情绪 (Social Sentiment):**
- One bullet per notable platform signal or theme (2-3 bullets)
- e.g. "X.com：AAPL/NVDA 情绪偏多，科技主线明显"
- Close with one bullet summarizing overall retail mood vs. F&G reading

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
（筛选维度：技术 + 情绪 + 期权流 + 基本面；O 无数据时降为 ≥2/3 可评估维度通过）

（本日无符合条件的候选 → 写"本日无符合标准的候选"；watchlist 和 UW 均无候选 → 写"本日无潜力股候选（指数平静，watchlist 无显著异动）"）

| Ticker | 技术(T) | 情绪(S) | 期权流(O) | 基本面(F) | 总分 |
|--------|---------|---------|----------|---------|------|
（✅ 通过 · ⚠️ N/A · ❌ 不符）

**简评：**
（每只候选一行：TICKER：[1-2 句信号来源及候选来源：UW/watchlist异动]）
```

**If it is a weekend**, write `wiki/market/<DATE>.md` with this structure instead:

```markdown
# 市场日报 · <DATE>（非交易日）

*由 `/market-daily` 自动生成。周末无行情数据，展示要闻与社交情绪。*

## 市场情绪
Fear & Greed: <score> (<label>) <direction_arrow> 昨日 <prev>

*0-24 极度恐慌 · 25-44 恐慌 · 45-55 中性 · 56-74 贪婪 · 75-100 极度贪婪*

（如数据不可用：`（数据不可用）`）

## 周末要闻
（新闻为空时写：`（今日新闻获取失败）`）
- [<title>](<url>) — 来源

## 社交情绪
| 平台 | 信号 | 主要话题 |
|------|------|---------|
| Reddit | Bullish / Neutral / Bearish | <主要讨论主题> |
| X.com | Bullish / Neutral / Bearish | <主要讨论主题> |
| 新闻情绪 | Bullish / Neutral / Bearish | <主要新闻情绪方向> |
| **综合** | **Bullish / Neutral / Bearish** | |

## AI 解读

**周末要闻解读：** <3-4 sentences summarizing themes and implications for next week>

**社交情绪：** <1-2 sentences on overall retail mood and any notable discussion heading into next week>
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
