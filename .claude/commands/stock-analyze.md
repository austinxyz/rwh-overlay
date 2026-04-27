# stock-analyze

Deep-dive analysis of a stock using finance-skills tools, producing wiki files that follow the 15-section thesis framework established in `wiki/tickers/WOLF/thesis.md`.

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
- Trend template score (how many of the 8 criteria pass)
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

Present the analysis in sections, one at a time. After presenting each section, wait for the user to reply with an affirmative (e.g., "ok", "next", "yes", "好", or any positive response) before presenting the next section. If the user requests changes to a section, revise it and re-present before moving on. Do not skip ahead. These sections map to the 15-section numbered framework used in the wiki:

**Section A — Business Overview**: What the company does, sector/industry, asset type (growth/value/speculative), one-line moat description. Maps to thesis §1 raison d'être.

**Section B — Financial Profile**: Key metrics table, revenue trend, margin profile, cash position and burn rate. Maps to thesis §2 financial metrics.

**Section C — Estimate Momentum**: Direction and magnitude of analyst estimate revisions. Bullish/neutral/bearish signal. Goes to financials.md.

**Section D — Earnings Track Record**: Last 4 quarters beat/miss history. Surprise magnitude. Next earnings date. Goes to financials.md.

**Section E — Technical Position**: SEPA stage, trend template score (8 criteria), key moving averages, current pattern if any. Actionable/Watch/Avoid. Maps to thesis §12 (BAIT T) and overview.md.

**Section F — Peers and Correlation**: Top correlated peers, relative performance. Maps to thesis §10 valuation comps and overview.md.

**Section G — Social Sentiment**: Cross-platform sentiment summary. Bullish/neutral/bearish. Maps to thesis §12 (BAIT B) and overview.md.

**Section H — Liquidity**: ADTV, estimated execution cost for a standard position. Goes to financials.md and thesis §11.

**Section I — Pivotal Investment Question**: One crisp question that determines whether the bull case works. Frame it as a binary: "Will X happen by Y date?" Maps to thesis §1.

**Section J — Bull / Base / Bear Cases**: Three scenarios with probability weights summing to 100%. For each: the key assumption, implied price target, and timeframe. Compute probability-weighted EV. Maps to thesis §13.

**Section K — Risk Factors**: Top 3–5 specific risks, not generic ones. Each risk should have a "tell" — what data point would confirm it's happening. Maps to thesis §8.

**Section L — Thesis-Break Triggers**: 3–5 specific, observable events that would cause immediate reassessment. Concrete (e.g. "Q2 revenue <$2M") not vague (e.g. "revenue disappoints"). Maps to thesis §15.

**Section M — Moat Assessment**: Narrow / Wide / None. Justify with specific competitive advantages, what competitors offer, and how durable the moat is. Maps to thesis §5.

**Section N — Capital Discipline**: Cash runway, dilution history, SBC as % of market cap, debt levels, management capital allocation track record. Maps to thesis §6.

**Section O — Action**: Current recommendation (Buy / Watch / Avoid / Trim) with specific price triggers, position sizing, and entry conditions. Maps to thesis §11 and §14.

After presenting all sections and getting user confirmation, proceed to Step 10.

### 10. Write wiki files

Use YYYY-MM-DD format for all date placeholders in file headers and changelog entries.

Reference `wiki/tickers/WOLF/thesis.md` as the canonical format example. Match its section headings, heading levels, table styles, and overall structure exactly.

Create or overwrite these files in `wiki/tickers/$ARGUMENTS/`:

---

#### `overview.md` — Lightweight summary card

Header:
```
# $ARGUMENTS — [Company Full Name]

**Last updated**: [today's date]
**Status**: [Active/Watch/Avoid] — [one-line description]
**Source of promotion**: [source if promoted from opinions/; omit if direct research]
**Language**: English | [中文](overview.zh.md)
```

Contents (match WOLF overview.md structure):
- **Business in One Line**: One sentence on what the company does and why it matters.
- **Asset Type**: Category label + brief explanation of valuation lens to use. Key metrics table (market cap, revenue, gross margin, operating margin/loss, trailing FCF, cash, total debt, beta, shares outstanding).
- **Moat**: Three subsections — "What [TICKER] has", "What [TICKER] doesn't have", "Verdict" — brief bullets only.
- **Technical Summary**: Compact SEPA snapshot table (price, 50/150/200MA values, % above 52-wk low, RS, trend template pass count, pattern, nearest valid entry, next earnings date). One-line SEPA verdict.
- **Peers and Relative Performance** (last 3 months): Table of top 4–5 correlated peers with 3-month return and latest price.
- **Social Sentiment**: Brief table (signal, reading, basis). Overall signal line.
- **Pivotal Investment Question**: The one binary question from Section I, in a blockquote.
- **Why It's In The Wiki**: Who surfaced it, when, their framing, and what the wiki adds (correction, balance, or endorsement). Pointer to thesis.md.

---

#### `thesis.md` — Full 15-section investment thesis

Header (match WOLF thesis.md exactly):
```
# $ARGUMENTS — Full Investment Thesis

**Ticker**: $ARGUMENTS ([Exchange])
**Company**: [Full Company Name]
**As of**: [today's date]
**Price**: $XX.XX (Yahoo Finance verified)
**52-wk range**: $XX.XX – $XX.XX
**Market cap**: $X.XXB
**Verdict**: [Speculative/Growth/Value] — [one-line verdict with price reference]
**Language**: English | [中文](thesis.zh.md)
```

Sections (numbered 1–15, matching WOLF heading style `## 1. Title`):

**§1. Why Does This Company Exist? + Pivotal Investment Question**
Raison d'être paragraph: the problem the company solves, why it matters now, and its strategic position as of today's date. Then the **Pivotal Question** in bold (from Section I). Include current milestone status (what has shipped, what is pending, what is the binary).

**§2. Annual Financial Metrics**
Three sub-tables:
- Income Statement (last 5 fiscal years): Revenue, Rev Growth YoY, Gross Profit, Gross Margin %, Operating Loss/Income, Operating Margin, Net Loss/Income, Diluted EPS, Diluted Shares. Include footnotes for any unusual items.
- Cash Flow (last 5 years): Operating CF, CapEx, Free Cash Flow, Stock-Based Comp.
- Balance Sheet (most recent year-end + post-raise estimate if applicable): Cash + ST Investments, Total Debt, Total Equity, Total Assets, Shares Outstanding. Add cash runway calculation.

**§3. Geographic Revenue Mix**
Revenue split by geography if available. If not disclosed for this company, write: "[Data gap: [period] [filing] geographic disclosure pending]" and note historical skew if known.

**§4. Revenue Mix & Business Model**
Product/segment roadmap table (Product, Speed/Spec, Target Market, Status, Volume Ramp timeline). Customer engagement stack table (Customer, Role, Status — use specific status language like "awaiting feedback", "production orders received", etc.). Business model mechanics paragraph (fabless/integrated, direct/channel, revenue model, gross margin structure at scale).

**§5. Competitive Moat**
- What makes this company's position defensible (IP, scale, distribution, switching costs, network effects).
- Direct competitors by business line (table where useful).
- What is eroding the moat (pricing pressure, new entrants, technology substitution).
- **Verdict**: Narrow / Wide / None with one-line justification and time horizon to verify.

**§6. Management & Leadership**
Key executives (name, role, tenure, notable background). Capital allocation track record — historical decisions and their outcomes. Post-restructuring or post-raise context if applicable. **Verdict** line: grade + rationale.

**§7. Strategic Growth Initiatives**
Three time horizons: Near-term (current FY remaining quarters), Medium-term (next 1–2 years), Long-term (3+ years). Numbered lists of concrete initiatives with expected timing.

**§8. Key Risks (Impact × Probability)**
Table: Risk | Impact (Critical/High/Medium) | Probability (%) | Composite. 6–8 rows. Include the most underappreciated risk as a callout paragraph below the table.

**§9. Industry-Specific Macro Analysis**
Market sizing (TAM with growth rate + source). End-market dynamics (2–4 sub-markets, trend for each). Competitive/pricing dynamic specific to this industry (e.g. Chinese competition in SiC, AI capex cycle for photonics). Regulatory/policy tailwinds or headwinds if material.

**§10. Valuation & Comparable Analysis**
- Current multiples table with context (what's typical for peers, what's unusual).
- Peer comparison table: Ticker | Mkt Cap | Rev TTM | EV/Rev | Growth TTM | GM% | Profitable?.
- Forward revenue scenario → implied share price table (3–4 scenarios × 3–4 multiples).
- Analyst consensus: number of analysts, rating distribution, median target vs current price, notable outlier notes.

**§11. Position Building Strategy**
Two sub-scenarios:
- **Scenario A** (if committed): Tranche table (Tranche | Trigger | Size | Form) with total cap.
- **Scenario B** (recommended): Current stance, specific wait conditions, what to watch before entering.
- Options vs stock guidance: when options make sense, IV context, specific guidance (LEAPS / short-dated / puts).

**§12. BAIT Framework (Mauboussin)**
Four subsections: B (Behavioral), A (Analytical), I (Informational), T (Technical). Each: 2–3 sentences of evidence + **Verdict** line. Then BAIT Overall paragraph comparing this stock to other wiki names in a mini table if ≥2 other speculative names exist.

**§13. Bull / Bear / Base Scenarios**
Three scenarios with probability % (must sum to 100%):
- Each scenario: probability, price target, % change, key assumption, revenue trajectory (FY+1, FY+2), implied multiple.
- Probability-Weighted EV calculation: `PW EV = (bull% × bull$) + (base% × base$) + (bear% × bear$)`.
- Comparison of PW EV to current price with interpretation.

**§14. Bottom Line**
- 1-year view: base case price + upside trigger + downside trigger.
- 3-year view: bull / base / bear price ranges.
- Portfolio allocation recommendation: target % at current price, form (stock/LEAPS), primary monitoring trigger.
- **Verdict** paragraph: final stance, what Yun Chen or the source got right / wrong, what to watch next. If currently holding from a lower level, specific profit-take guidance.

**§15. Monitoring Checklist**
Three subsections with checkbox items:
- **Near-term (next 60 days)**: Named catalyst (e.g. Q1 2026 earnings) with specific pass/fail metrics for each item.
- **Mid-term**: Named catalysts with pass/fail metrics.
- **Thesis-break triggers**: 4–6 concrete, observable events (with specific numeric thresholds) that would cause immediate reassessment (any ONE = reconsider).
- **Continuing thesis-strength triggers** (optional): 3–4 events that would increase conviction.

Close with Sources block: bulleted list of all data sources used (Yahoo Finance, stockanalysis.com, IR press releases, analyst notes, opinion sources).

Flag any **Data gaps** that should be filled at next update.

---

#### `financials.md` — Detailed data tables

Header:
```
# $ARGUMENTS — Key Financial Metrics

**Last updated**: [today's date]
**Data source**: [sources used]
**Next update trigger**: [next catalyst, e.g. Q1 2026 earnings — May 14, 2026]
**Language**: English | [中文](financials.zh.md)
```

Contents (match WOLF financials.md structure, add estimate/earnings/liquidity sections):
1. **Critical Context** — only if the company has unusual accounting (restructuring, fresh-start, SPACs, etc.). Omit section entirely if nothing unusual.
2. **Price & Market Data** — compact table: price, today's change, 52-wk range, position vs 52-wk, market cap, avg volume, beta, EPS TTM, P/E, analyst median target.
3. **Annual Income Statement** — same table as thesis §2, with footnotes.
4. **Gross Margin Trend** — compact table showing GM% by year with one-line commentary per year. Omit if margin is stable and uninteresting.
5. **Annual Cash Flow** — same table as thesis §2. Commentary on peak-burn year, post-raise expectations.
6. **Balance Sheet** — pre/post comparison if restructuring; otherwise single table as in thesis §2. Include runway calculation.
7. **Quarterly Context** — last 4 quarters of revenue, operating loss/income, net income, key notes. Include upcoming quarter guide if available.
8. **Dilution History** — table: Year | Shares | YoY % | Source. Note cumulative dilution.
9. **Estimate Momentum** (from Section C) — EPS estimates table by period (avg, low, high, YoY growth, # analysts). Revenue estimates table. EPS revision trend table (90d/30d/7d/current). Revision breadth. Overall signal.
10. **Earnings Track Record** (from Section D) — table: Quarter | EPS Estimate | EPS Actual | Surprise % | Revenue. Note on any unusual miss/beat drivers. Next earnings date + consensus.
11. **Liquidity** (from Section H) — table: ADTV, median volume, dollar volume, float turnover, daily volatility, short %, short ratio, $50K impact. Liquidity grade.
12. **Valuation Sensitivity** — implied revenue to justify current price (table: multiple × required revenue × year achievable). Forward revenue scenario → share price table.
13. **Analyst Consensus** — number of analysts, rating distribution, average vs median target, notable outlier details.
14. **Peer Comparison** — table matching thesis §10.
15. **Upcoming Catalysts** — table: Date | Event | What to Watch.
16. **Sources** — bulleted list.

---

#### `changelog.md`

If it already exists, prepend a new entry at the top (newest-first). If it does not exist, create with a single initial entry.

Entry format:
```markdown
## [TODAY'S DATE] — [Brief label, e.g. "Initial Analysis" or "Full Refresh"] (via /stock-analyze)

[One-line summary: most important finding, price at time of analysis, key verdict change if refresh]
```

---

### 11. Write Chinese translations

For each of `overview.md`, `thesis.md`, `financials.md`, create or overwrite the corresponding `.zh.md` file:
- Same structure and all data identical to the English version
- All prose translated to Chinese; table headers and numeric data stay as-is
- File headers include language back-link:
  - `overview.zh.md`: `**语言**: 中文 | [English](overview.md)`
  - `thesis.zh.md`: `**语言**: 中文 | [English](thesis.md)`
  - `financials.zh.md`: `**语言**: 中文 | [English](financials.md)`

Also update `changelog.zh.md` to match the English changelog entry (translated).

### 12. Confirm completion

Report: "分析完成：`wiki/tickers/$ARGUMENTS/` 已更新（overview + thesis + financials，含中文版）"
