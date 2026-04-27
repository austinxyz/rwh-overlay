# market-monthly

Generate the monthly market report: review this month's performance, track Chen Yun opinion hit rate, assess potential stock candidate accuracy, and outline next month's outlook. Writes to `wiki/market/`.

## Arguments

Optional: `--month YYYY-MM` to generate a report for a specific month. Otherwise uses the current month.

## Steps

### 1. Determine report month

If `--month` was passed, use that value. Otherwise compute the current month:

```bash
python -c "import datetime; print(datetime.date.today().strftime('%Y-%m'))"
```

Compute the month's first and last calendar dates:

```bash
python -c "import datetime, calendar; y, m = map(int, '<MONTH>'.split('-')); first = datetime.date(y, m, 1); last = datetime.date(y, m, calendar.monthrange(y, m)[1]); print(first.strftime('%Y-%m-%d'), last.strftime('%Y-%m-%d'))"
```

Output filename: `wiki/market/monthly-<MONTH>.md`

### 2. Check for existing report

Check if `wiki/market/monthly-<MONTH>.md` already exists. If so, ask the user whether to overwrite before proceeding.

### 3. Read this month's daily reports

List all files in `wiki/market/` matching `<MONTH>-*.md` (excluding `weekly-*`, `monthly-*`, `quarterly-*`, and `index.md`). Read each.

Extract and aggregate:
- Fear & Greed score per day (list; compute monthly average, min, max)
- Index pct changes per day (to reconstruct approximate monthly trajectories)
- AI commentary highlights (一句话 per trading day's 市场概况)
- All watchlist tickers with notable daily moves (>2%)
- All tickers that appeared in 今日潜力股候选 sections: ticker name, date of appearance, score (X/4)

Count how many trading day reports exist for the month.

### 4. Fetch monthly index and watchlist performance

Use the `yfinance-data` skill to get monthly returns (first trading day of month open to last trading day close, or today if month is ongoing) for:
- SPY, QQQ, DIA, IWM

For each watchlist ticker (files in `wiki/tickers/`): monthly return, monthly high/low, current price vs 50MA.

### 5. Track potential stock candidate hit rate

For all tickers collected from 今日潜力股候选 sections in Step 3:
- Use `yfinance-data` to get their return from the date of signal to end of month (or today if month is ongoing)
- Compare each against SPY return for the same window
- Classify: **Hit** (positive alpha vs SPY and positive absolute return) / **Miss** (negative alpha or negative absolute) / **Too soon** (appeared in last 5 trading days, window too short)
- Compute: Hit rate = Hits / (Hits + Misses)

### 6. Review Chen Yun opinions for the month

List all files in `wiki/opinions/chen-yun-log/` matching `<MONTH>-*.md`. Read each.

For each:
- Collect all tickers mentioned
- Note recommendation strength (🔥 count)
- Note validation status (待验证 / ✅ 已验证)

For validated tickers: use `yfinance-data` to get price change from the date of Chen's mention to end of month. Classify direction: Up / Down (relative to mention date close).

Compute: Chen hit rate = count(validated + price moved up from mention date) / count(validated total)

### 7. Assess watchlist thesis alignment

For each ticker in `wiki/tickers/`, read its `thesis.md` and `changelog.md`. Note:
- Whether the month's events strengthened or weakened the thesis (scan the §15 monitoring checklist if visible)
- Any significant divergence between actual price action and thesis scenarios

### 8. Analyze and write AI commentary

Write these sections:

**月度回顾 (Monthly Review):**
- Overall market narrative: where did the market start, how did it evolve, where did it finish?
- Key macro drivers this month (Fed, economic data, geopolitics, earnings)
- Sector rotation theme: which sectors led and which lagged persistently?
- Keep to 4-5 sentences.

**Watchlist 月度表现 (Watchlist Monthly):**
- For each watchlist ticker: monthly return and 1-sentence thesis alignment comment.
- Flag any ticker where the thesis materially changed this month.

**陈云月度复盘 (Chen Yun Monthly Retrospective):**
- Number of tickers pushed and validated
- Hit rate with brief commentary on the best and worst calls
- Any themes in his accuracy (which sectors/types he got right or wrong)

**潜力股胜率 (Potential Stock Hit Rate):**
- Monthly hit rate with brief context on what worked (which dimensions: T/S/O/F)
- If no candidates appeared this month, note it.

**下月展望 (Next Month Outlook):**
- Current market technical posture (above/below key MAs, trend direction)
- Key upcoming macro events (Fed meeting, CPI, employment)
- Watchlist tickers approaching key catalysts next month
- Any watchlist additions or removals warranted by this month's data?
- Keep to 4-5 sentences.

### 9. Write the monthly report

Write `wiki/market/monthly-<MONTH>.md`:

```markdown
# 市场月报 · <MONTH>

*由 `/market-monthly` 自动生成。*

## 本月市场情绪
Fear & Greed 月均：<avg> | 区间：<min>–<max>
日报覆盖：<N> 个交易日

## 主要指数月表现
| 指数 | 月涨跌幅 | 月收盘 |
|------|---------|--------|
| SPY | +X.XX% | $XXX.XX |
| QQQ | +X.XX% | $XXX.XX |
| DIA | +X.XX% | $XXX.XX |
| IWM | +X.XX% | $XXX.XX |

## Watchlist 月度表现
| Ticker | 月涨跌幅 | 月收盘 | 论文对齐 | 备注 |
|--------|---------|--------|---------|------|
（论文对齐：✅ 符合 / ⚠️ 部分 / ❌ 背离 / — 无显著变化）

## 今日潜力股候选月度胜率

本月出现 <N> 只候选（含重复）

| Ticker | 出现次数 | 月度表现 | vs SPY | 结果 |
|--------|---------|---------|--------|------|

**月度胜率：** <Hits>/<Hits+Misses> = XX%
（本月无候选 → 本月日报无潜力股候选记录）

## 陈云观点月度复盘

本月提及 <N> 只标的，已验证 <M> 只

| Ticker | 推荐强度 | 验证状态 | 提及日至月末涨跌 |
|--------|---------|---------|----------------|

**月度命中率：** <Hits>/<validated total> = XX%（方向正确 / 已验证中）

## AI 解读

**月度回顾：** <4-5 sentences>

**Watchlist 月度表现：** <highlights and thesis alignment>

**陈云月度复盘：** <hit rate commentary and notable calls>

**潜力股胜率解读：** <context on what worked or "本月无候选记录">

**下月展望：** <4-5 sentences>
```

### 10. Confirm completion

Report: "市场月报已生成：`wiki/market/monthly-<MONTH>.md`"
