# stock-refresh

Refresh an existing ticker's analysis when new information arrives (earnings release, filing, guidance change, major news). Updates only the sections that changed — does not rebuild the full thesis from scratch.

If no prior analysis exists under `wiki/tickers/$ARGUMENTS/`, stop and suggest running `/stock-analyze $ARGUMENTS` instead.

## Arguments

Required: `<TICKER>` — the stock symbol (e.g. `POET`, `NVDA`).

Optional trigger hint appended after the ticker (e.g. `POET earnings`, `NVDA guidance cut`). If omitted, ask the user what triggered the refresh before proceeding.

## Steps

### 1. Normalize and read existing analysis

Normalize `$ARGUMENTS` ticker portion to uppercase.

Check that `wiki/tickers/$ARGUMENTS/` exists. If it does not, stop:

> "No existing analysis found for $ARGUMENTS. Run `/stock-analyze $ARGUMENTS` to build one from scratch."

Read all existing files:
- `wiki/tickers/$ARGUMENTS/overview.md`
- `wiki/tickers/$ARGUMENTS/thesis.md`
- `wiki/tickers/$ARGUMENTS/financials.md`
- `wiki/tickers/$ARGUMENTS/changelog.md`

Extract and note: previous verdict (Buy/Watch/Avoid), previous price at analysis date, previous thesis-break triggers, previous monitoring checklist open items.

### 2. Confirm refresh trigger

If the user did not provide a trigger hint, ask:

> "什么触发了这次刷新？（例如：财报发布、10-Q、指引变化、重大新闻、价格大幅变动）"

Wait for the user's response. The trigger determines which data to fetch in Step 3.

### 3. Fetch fresh data (targeted, not full suite)

Always fetch:
- Current price, 52-week range, volume (via `yfinance-data`)
- Latest EPS and revenue actuals vs estimates, next earnings date (via `earnings-recap` and `earnings-preview`)
- Current estimate revision trend — last 30 days (via `estimate-analysis`)

Fetch additionally based on trigger:
- **Earnings / filing**: quarterly income statement, cash flow, balance sheet update (via `yfinance-data`)
- **Guidance change / macro**: analyst price target and rating changes (via `yfinance-data`)
- **Price move / technical**: SEPA stage and trend template score update (via `sepa-strategy`)
- **News / sentiment**: cross-platform sentiment signal update (via `finance-sentiment`)

Do not re-run skills that are unrelated to the trigger.

### 4. Present delta summary

Before writing any files, present a concise delta report:

```
## $ARGUMENTS Refresh Summary — [TODAY'S DATE]
触发：[trigger description]

### 数据变化
| 指标 | 上次分析 | 当前 |
|------|---------|------|
| 价格 | $XX.XX (prior date) | $XX.XX |
| 市值 | $X.XXB | $X.XXB |
| 最近季报 EPS | [prior] | [actual] ([beat/miss X%]) |
| 最近季报收入 | [prior] | [actual] ([beat/miss X%]) |
| 估值修正方向 | [prior] | [current 30d trend] |
| 技术阶段 | Stage X | Stage X |（仅在 technical 触发时显示）

### 论点影响评估
- **Thesis-break 触发检查**: [any prior triggers hit? list them]
- **监控清单进展**: [any items resolved or newly flagged?]
- **论点完整性**: [Intact / Weakened / Strengthened / Broken] — [one sentence why]
- **建议操作变化**: [unchanged / Buy→Watch / Watch→Avoid / etc.]
```

Ask: "以上内容确认后写入文件？（yes / no，或提出修改意见）"

Wait for explicit confirmation. If the user requests changes, revise and re-present. Do not write files until confirmed.

### 5. Update financials.md

Use YYYY-MM-DD format for all dates.

Update these sections in-place (do not rewrite the whole file):
- **Price & Market Data** — replace with current values
- **Estimate Momentum** — replace with latest 30-day revision data
- **Earnings Track Record** — prepend latest quarter row (keep prior rows)
- **Upcoming Catalysts** — update next earnings date and any known catalysts
- If earnings trigger: update **Quarterly Context**, **Annual Income Statement**, **Annual Cash Flow**, **Balance Sheet** with new actuals

Update the file header:
```
**Last updated**: [TODAY'S DATE]
**Next update trigger**: [next catalyst, e.g. Q2 2026 earnings — Aug XX, 2026]
```

### 6. Update thesis.md (targeted sections only)

Update only sections affected by the new data. Leave unaffected sections untouched.

Common refresh targets:
- **§2 Annual Financial Metrics**: add new quarterly actuals if earnings trigger
- **§8 Key Risks**: adjust probability % if any risk materialized or receded
- **§13 Bull / Bear / Base Scenarios**: update price targets and PW EV if fundamentals shifted
- **§14 Bottom Line**: update verdict line and 1-year view if recommendation changed
- **§15 Monitoring Checklist**: check off resolved items; add new items from latest earnings call or filing

If the overall thesis verdict changes (e.g., Watch → Avoid), update the thesis.md header **Verdict** field.

### 7. Update overview.md (targeted sections only)

Update only sections affected by the new data:
- **Technical Summary**: update price, MA values, SEPA snapshot if technical data was fetched
- **Asset Type** key metrics table: update market cap, revenue, margin
- Status line in header: update if verdict changed

```
**Status**: [Active/Watch/Avoid] — [updated one-line description]
**Last updated**: [TODAY'S DATE]
```

### 8. Update changelog

Prepend a new entry at the top (newest-first) in `changelog.md`:

```markdown
## [TODAY'S DATE] — [Trigger Label] (via /stock-refresh)

[One sentence: what changed and what it means for the thesis. E.g. "Q1 beat on revenue (+8% vs est) but guided Q2 below consensus — thesis intact but timeline extended."]
**前次论点状态**: [prior verdict] → **更新后**: [new verdict if changed, otherwise "不变"]
```

### 9. Update Chinese translations

For each file modified in Steps 5–8, update the corresponding `.zh.md` file:
- Same sections updated, same data
- All prose translated to Chinese; table headers and numeric data stay as-is

If a `.zh.md` file does not exist for a modified file, create it now (translate the full updated English file).

### 10. Confirm completion

Report:
```
刷新完成：wiki/tickers/$ARGUMENTS/
- financials.md 已更新（[list updated sections]）
- thesis.md 已更新（[list updated sections]）
- overview.md 已更新（[list updated sections]）
- changelog.md 已追加
- 中文版已同步
论点状态：[prior verdict] → [new verdict or "不变"]
```
