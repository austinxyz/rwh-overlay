# market-quarterly

Generate the quarterly market report: deep review of the quarter's performance, thesis validation for each watchlist holding, earnings season analysis, SaaS/tech valuation assessment, and next quarter outlook. Writes to `wiki/market/`.

## Arguments

Optional: `--quarter YYYY-QX` to generate a report for a specific quarter (e.g. `--quarter 2026-Q1`). Otherwise uses the current quarter.

## Steps

### 1. Determine report quarter

If `--quarter` was passed, use that value. Otherwise compute the current quarter:

```bash
python -c "import datetime; today = datetime.date.today(); q = (today.month - 1) // 3 + 1; print(f'{today.year}-Q{q}')"
```

Determine the quarter's months (Q1 = Jan–Mar, Q2 = Apr–Jun, Q3 = Jul–Sep, Q4 = Oct–Dec) and its first and last dates.

Output filename: `wiki/market/quarterly-<QUARTER>.md`

### 2. Check for existing report

Check if `wiki/market/quarterly-<QUARTER>.md` already exists. If so, ask the user whether to overwrite before proceeding.

### 3. Read monthly reports for the quarter

List all `wiki/market/monthly-<YEAR>-<MM>.md` files for this quarter's three months. Read each that exists. Extract:
- Monthly Fear & Greed averages and ranges
- Monthly index returns (SPY, QQQ, DIA, IWM)
- Chen Yun hit rates per month
- Potential stock candidate hit rates per month
- Key narrative themes per month (1-2 sentences per month's 月度回顾)

If monthly reports don't exist, note that quarterly data will be assembled from daily reports directly (more limited).

### 4. Fetch quarterly index and watchlist performance

Use the `yfinance-data` skill to get quarterly returns (first trading day of quarter open to last trading day close, or today if quarter is ongoing) for:
- SPY, QQQ, DIA, IWM

For each watchlist ticker (files in `wiki/tickers/`): quarterly return, quarterly high/low, current Stage vs quarter start, position vs 50/150/200MA.

### 5. Earnings season analysis

For this quarter's reporting period (earnings are typically reported in the first 1-2 months of each quarter for the prior quarter's results), use the `earnings-recap` skill for all watchlist tickers to get:
- EPS result vs consensus (beat / miss / in-line, magnitude)
- Revenue result vs consensus
- Guidance direction: raised / maintained / lowered / none given
- Stock reaction: day-after pct change

Also use the `estimate-analysis` skill to assess broader trends: which sectors showed the most upward vs downward estimate revisions this quarter?

### 6. Thesis validation for each watchlist holding

For each ticker in `wiki/tickers/` (read its `thesis.md` and `changelog.md`):

Assess against the §15 Monitoring Checklist:
- Which near-term catalysts from the checklist were due this quarter? Did they trigger?
- Did any thesis-break triggers fire?
- Is the current price within or outside the range implied by the bull/base/bear scenarios?
- Summarize in one of four verdicts: **完好** (intact) / **减弱** (weakened — thesis still valid but with lower confidence) / **破位** (broken — a thesis-break trigger fired) / **加速** (accelerated — bull case materializing faster than expected)

### 7. SaaS and tech valuation analysis (if applicable)

If any watchlist tickers are SaaS, software, or high-multiple tech names, use the `saas-valuation-compression` skill to assess:
- How did EV/Revenue and EV/NTM Revenue multiples change this quarter?
- Is valuation compression continuing, stabilizing, or reversing?
- What revenue growth rate is required to sustain current multiples?

Skip this step if no watchlist tickers qualify.

### 8. Macro outlook for next quarter

Use the `yfinance-data` skill to get current macro indicators:
- Fed Funds Rate (current level, next FOMC meeting date)
- 10Y Treasury yield and 2Y–10Y spread (yield curve shape)
- DXY trend (dollar strength)
- HYG trend (credit spread proxy)
- VIX level and trend (volatility regime)

Assess: which sectors tend to outperform in the next quarter given the current macro setup? What are the 3 biggest macro risks?

### 9. Analyze and write AI commentary

Write these sections:

**季度回顾 (Quarterly Review):**
- Where did the quarter start and end for markets?
- What were the 2-3 dominant macro or geopolitical themes?
- How did the quarter evolve (e.g. volatile start, recovery, range-bound)?
- Keep to 5-6 sentences.

**Watchlist 季度表现 (Watchlist Quarterly):**
- For each watchlist ticker: quarterly return vs SPY, thesis verdict, key catalyst outcome.
- Note any thesis changes and their trigger.

**财报季分析 (Earnings Season Analysis):**
- Overall beat/miss rates across sectors
- Most significant individual beats and misses
- How guidance trended overall (cautious vs confident)
- Keep to 3-4 sentences.

**论文有效性更新 (Thesis Validity Updates):**
- For tickers where thesis changed: what fired, what it means, updated stance going forward.
- Concrete: "TICKER moved from Watch to Avoid because [specific trigger]"

**估值分析 (Valuation Analysis, if applicable):**
- Multiple compression or expansion trends for SaaS/tech names
- What the market is implying about growth vs value premium

**下季展望 (Next Quarter Outlook):**
- Key macro theme likely to dominate
- Fed path and rate impact on growth vs value rotation
- Major upcoming earnings for watchlist names
- Watchlist adjustments: any additions or removals warranted?
- Keep to 5-6 sentences.

### 10. Write the quarterly report

Write `wiki/market/quarterly-<QUARTER>.md`:

```markdown
# 市场季报 · <QUARTER>

*由 `/market-quarterly` 自动生成。*

## 本季市场情绪
（来自各月报汇总；如月报缺失则标注：月报数据不完整）
Fear & Greed 季均：<avg> | 月均区间：<M1 avg>–<M2 avg>–<M3 avg>

## 主要指数季度表现
| 指数 | 季涨跌幅 | 季收盘 | vs SPY |
|------|---------|--------|--------|
| SPY | +X.XX% | $XXX.XX | — |
| QQQ | +X.XX% | $XXX.XX | +X.XX% |
| DIA | +X.XX% | $XXX.XX | +X.XX% |
| IWM | +X.XX% | $XXX.XX | +X.XX% |

## Watchlist 季度表现
| Ticker | 季涨跌幅 | vs SPY | 论文状态 | 关键催化剂结果 |
|--------|---------|--------|---------|--------------|
（论文状态：完好 / 减弱 / 破位 / 加速）

## 财报季分析

### 板块层面
| 板块 | EPS 超预期率 | 营收超预期率 | 指引方向 |
|------|------------|------------|---------|

### Watchlist 个股财报
| Ticker | EPS 结果 | 营收结果 | 指引 | 当日反应 |
|--------|---------|---------|------|---------|
（未发布财报的标注 — ）

## 论文有效性更新

[For each ticker with verdict change:]
**TICKER：** [旧状态] → [新状态]
[1-2 sentences: what triggered the change and updated monitoring focus]

（无状态变化：本季所有论文状态无实质性变化）

## 估值分析（SaaS / 高倍数科技，如适用）

[EV/Revenue multiple trends, compression/expansion, implied growth requirement]

（无适用标的：略去本节）

## 季度潜力股候选汇总

| 月份 | 候选数 | 胜率 | 备注 |
|------|-------|------|------|
（数据来自各月报；月报缺失则标注 N/A）

## 陈云季度命中率

| 月份 | 验证数 | 命中数 | 月度命中率 |
|------|-------|-------|---------|
（数据来自各月报）

## AI 解读

**季度回顾：** <5-6 sentences>

**财报季分析：** <3-4 sentences>

**论文有效性更新：** <key changes with one-line verdict per changed ticker>

**下季展望：** <5-6 sentences>

## 宏观快照（下季参考）

| 指标 | 当前值 | 趋势 |
|------|--------|------|
| Fed Funds Rate | X.XX% | [加息/不变/降息路径] |
| 10Y Yield | X.XX% | [升/降] |
| 2Y–10Y Spread | ±X bps | [正常/倒挂] |
| DXY | XXX.X | [强/弱] |
| VIX | XX.X | [低位/中位/高位] |
```

### 11. Confirm completion

Report: "市场季报已生成：`wiki/market/quarterly-<QUARTER>.md`"
