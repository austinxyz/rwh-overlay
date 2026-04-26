# stock-analyze

Deep-dive analysis of a stock using finance-skills tools, producing wiki files that follow the upstream 15-section thesis framework.

## Arguments

Required: `<TICKER>` — the stock symbol to analyze (e.g. `POET`, `NVDA`).

## Steps

### 1. Confirm ticker and check existing wiki

Normalize `$ARGUMENTS` to uppercase before use in all file paths and headers (e.g., `nvda` → `NVDA`).

Check if `wiki/tickers/$ARGUMENTS/` already exists. If it does, read the existing `overview.md`, `thesis.md`, and `financials.md` so you understand the current state before updating. Tell the user what you found ("Existing analysis found from [date]" or "No existing analysis — starting fresh").

### 2. Fetch fundamental data

Use the `yfinance-data` skill to fetch:
- Company overview: name, sector, industry, description, market cap, employees
- Financial statements: income statement (last 4 quarters + annual), balance sheet, cash flow
- Key metrics: P/E, P/S, EV/EBITDA, gross margin, operating margin, revenue growth YoY
- Analyst ratings: consensus recommendation, price targets (low / median / high)

### 3. Analyze estimate trends

Use the `estimate-analysis` skill to determine:
- Direction of EPS and revenue estimate revisions over the last 90 days (up / flat / down)
- Estimate spread (bull vs bear range)
- Whether estimates are accelerating or decelerating

### 4. Earnings history and next event

Use the `earnings-recap` skill to get the last 4 quarters of actual vs estimated EPS and revenue (beat/miss/magnitude).

Use the `earnings-preview` skill to get the next earnings date and current analyst consensus.

### 5. Technical analysis (SEPA)

Use the `sepa-strategy` skill to evaluate:
- Current stage (Stage 1 / 2 / 3 / 4)
- Trend template score (how many of the 7 criteria pass)
- Current price vs 50MA / 150MA / 200MA
- Any recognizable pattern (VCP, cup-with-handle, flat base, bull flag)
- Overall technical verdict: Actionable / Watch / Avoid

### 6. Correlation and peers

Use the `stock-correlation` skill to identify:
- Top 3–5 correlated peers (by sector/thematic)
- How the stock has performed vs its peers over the last 3 months

### 7. Social sentiment

Use the `finance-sentiment` skill to get:
- Current Reddit mention count and sentiment score
- Current X.com (Twitter) mention count and sentiment score
- News sentiment score
- Overall social signal: Bullish / Neutral / Bearish

### 8. Liquidity

Use the `stock-liquidity` skill to assess:
- Average daily dollar volume (ADTV)
- Bid-ask spread estimate
- Estimated market impact for a $50K order

### 9. Synthesize and present draft

Present the analysis in sections, one at a time. After presenting each section, wait for the user to reply with an affirmative (e.g., "ok", "next", "yes", "好", or any positive response) before presenting the next section. If the user requests changes to a section, revise it and re-present before moving on. Do not skip ahead. Sections follow the upstream thesis framework:

**Section A — Business Overview**: What the company does, sector/industry, asset type (growth/value/speculative), one-line moat description.

**Section B — Financial Profile**: Key metrics table, revenue trend, margin profile, cash position and burn rate.

**Section C — Estimate Momentum**: Direction and magnitude of analyst estimate revisions. Bullish/neutral/bearish signal.

**Section D — Earnings Track Record**: Last 4 quarters beat/miss history. Surprise magnitude. Next earnings date.

**Section E — Technical Position**: SEPA stage, trend template score, key moving averages, current pattern if any. Actionable/Watch/Avoid.

**Section F — Peers and Correlation**: Top correlated peers, relative performance.

**Section G — Social Sentiment**: Cross-platform sentiment summary. Bullish/neutral/bearish.

**Section H — Liquidity**: ADTV, estimated execution cost for a standard position.

**Section I — Pivotal Investment Question**: One crisp question that determines whether the bull case works. Frame it as a binary: "Will X happen by Y date?"

**Section J — Bull / Base / Bear Cases**: Three scenarios with probability weights summing to 100%. For each: the key assumption, implied price target, and timeframe.

**Section K — Risk Factors**: Top 3–5 specific risks, not generic ones. Each risk should have a "tell" — what data point would confirm it's happening.

**Section L — Thesis-Break Triggers**: 3–5 specific, observable events that would cause immediate reassessment. Concrete (e.g. "Q2 revenue <$2M") not vague (e.g. "revenue disappoints").

**Section M — Moat Assessment**: Narrow / Wide / None. Justify with specific competitive advantages and how durable they are.

**Section N — Capital Discipline**: Cash runway, dilution history, SBC as % of market cap, debt levels.

**Section O — Action**: Current recommendation (Buy / Watch / Avoid / Trim) with specific conditions that would change it.

After presenting all sections and getting user confirmation, proceed to Step 10.

### 10. Write wiki files

Use YYYY-MM-DD format for all date placeholders (e.g. `[today's date]`) in file headers and changelog entries.

Create or overwrite these files in `wiki/tickers/$ARGUMENTS/`:

**`overview.md`**: Contains Sections A, B, E (technical), F (peers), G (sentiment). Header format:
```
# $ARGUMENTS — [Company Full Name]

**Last updated**: [today's date]
**Status**: [Active/Watch/Avoid] — [one-line description]
**Language**: English | [中文](overview.zh.md)
```

**`thesis.md`**: Contains Sections I through O (the full investment thesis). Header format:
```
# $ARGUMENTS — Investment Thesis

**Last updated**: [today's date]
**Ticker**: $ARGUMENTS
**Status**: [Active/Watch/Avoid]
**Language**: English | [中文](thesis.zh.md)
```

Match the header fields used in any existing thesis.md files in the repo for consistency.

**`financials.md`**: Contains Sections C, D, H (estimates, earnings, liquidity) plus full financial tables from Step 2. Header format:
```
# $ARGUMENTS — Financials

**Last updated**: [today's date]
**Language**: English | [中文](financials.zh.md)
```

**`changelog.md`**: If it already exists, append a new entry at the top (newest-first) with today's date and a one-line summary of what was analyzed or updated. If it does not exist, create it with a single initial entry. Entry format:

```markdown
## [TODAY'S DATE] — Initial Analysis (via /stock-analyze)

[One-line summary of key finding, e.g., "Stage 2 breakout candidate; Q2 2026 revenue ramp is the pivotal catalyst"]
```

### 11. Write Chinese translations

For each of `overview.md`, `thesis.md`, `financials.md`, create the corresponding `.zh.md` file with:
- Same structure and data as the English version
- All prose translated to Chinese
- Each file's header includes a back-link to its English counterpart:
  - `overview.zh.md`: `**语言**: 中文 | [English](overview.md)`
  - `thesis.zh.md`: `**语言**: 中文 | [English](thesis.md)`
  - `financials.zh.md`: `**语言**: 中文 | [English](financials.md)`

### 12. Confirm completion

Report: "分析完成：`wiki/tickers/$ARGUMENTS/` 已更新（overview + thesis + financials，含中文版）"
