# Phase 1 Research Commands Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 4 Claude Code slash commands that integrate finance-skills into the rwh-overlay research workflow: `/stock-analyze`, `/stock-entry`, `/chen-integrate`, `/chen-validate`.

**Architecture:** Each command is a Markdown instruction file in `.claude/commands/`. Claude reads the file when the slash command is invoked and follows the instructions, calling finance-skills via natural language and writing output to `wiki/`. No Python scripts needed — all logic lives in the command Markdown.

**Tech Stack:** Claude Code slash commands (Markdown), finance-skills plugin (yfinance-data, estimate-analysis, earnings-recap/preview, sepa-strategy, stock-correlation, finance-sentiment, stock-liquidity, twitter-reader, unusual_whales Telegram bot via tdl), existing `wiki/` file structure.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `.claude/commands/stock-analyze.md` | Create | `/stock-analyze <TICKER>` command |
| `.claude/commands/stock-entry.md` | Create | `/stock-entry <TICKER>` command |
| `.claude/commands/chen-integrate.md` | Create | `/chen-integrate` command |
| `.claude/commands/chen-validate.md` | Create | `/chen-validate <TICKER>` command |
| `wiki/tickers/<TICKER>/overview.md` | Modified by command | Adds "历史入场分析" section |
| `wiki/tickers/<TICKER>/changelog.md` | Modified by command | Appends entry record |
| `wiki/tickers/<TICKER>/entry-YYYY-MM-DD.md` | Created by command | Entry point analysis |
| `wiki/opinions/chen-yun-log/YYYY-MM-DD.md` | Created/Modified by command | Daily log + validation results |

---

## Task 1: `/stock-analyze` command

**Files:**
- Create: `.claude/commands/stock-analyze.md`

- [ ] **Step 1: Review the existing command format**

Read `.claude/commands/market-daily.md` to confirm command file conventions (argument handling via `$ARGUMENTS`, step structure, bash block usage).

- [ ] **Step 2: Write the command file**

Create `.claude/commands/stock-analyze.md` with this exact content:

```markdown
# stock-analyze

Deep-dive analysis of a stock using finance-skills tools, producing wiki files that follow the upstream 15-section thesis framework.

## Arguments

Required: `<TICKER>` — the stock symbol to analyze (e.g. `POET`, `NVDA`).

## Steps

### 1. Confirm ticker and check existing wiki

Check if `wiki/tickers/$ARGUMENTS/` already exists. If it does, read the existing `overview.md` and `thesis.md` so you understand the current state before updating. Tell the user what you found ("Existing analysis found from [date]" or "No existing analysis — starting fresh").

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

Present the analysis in sections, one at a time, asking for user confirmation after each section before proceeding. Sections follow the upstream thesis framework:

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

Create or overwrite these files in `wiki/tickers/$ARGUMENTS/`:

**`overview.md`**: Contains Sections A, B, E (technical), G (sentiment). Header format:
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
**Language**: English | [中文](thesis.zh.md)
```

**`financials.md`**: Contains Sections C, D, H (estimates, earnings, liquidity) plus full financial tables from Step 2. Header format:
```
# $ARGUMENTS — Financials

**Last updated**: [today's date]
**Language**: English | [中文](financials.zh.md)
```

### 11. Write Chinese translations

For each of `overview.md`, `thesis.md`, `financials.md`, create the corresponding `.zh.md` file with:
- Same structure and data as the English version
- All prose translated to Chinese
- Header includes: `**语言**: 中文 | [English](overview.md)`

### 12. Confirm completion

Report: "分析完成：`wiki/tickers/$ARGUMENTS/` 已更新（overview + thesis + financials，含中文版）"
```

- [ ] **Step 3: Smoke test with POET**

Run `/stock-analyze POET` and verify:
- Each of the 8 data-fetch steps runs without error
- Each section A–O is presented and confirmed
- `wiki/tickers/POET/overview.md` is updated with today's date
- `wiki/tickers/POET/thesis.md` is updated
- `wiki/tickers/POET/financials.md` is updated
- All three `.zh.md` files are created/updated

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/stock-analyze.md
git commit -m "feat: add /stock-analyze command with finance-skills integration"
```

---

## Task 2: `/stock-entry` command

**Files:**
- Create: `.claude/commands/stock-entry.md`
- Modified by command: `wiki/tickers/<TICKER>/entry-YYYY-MM-DD.md` (created)
- Modified by command: `wiki/tickers/<TICKER>/changelog.md` (appended)
- Modified by command: `wiki/tickers/<TICKER>/overview.md` (link added)

- [ ] **Step 1: Write the command file**

Create `.claude/commands/stock-entry.md` with this exact content:

```markdown
# stock-entry

Generate a specific entry/exit point analysis for a ticker: entry zone, stop loss, price targets, position sizing, and key option market levels. Writes a dated file to the ticker's wiki directory and updates changelog and overview.

## Arguments

Required: `<TICKER>` — the stock symbol (e.g. `POET`, `NVDA`).

## Steps

### 1. Check existing research

Read `wiki/tickers/$ARGUMENTS/overview.md` if it exists. Extract current thesis status and any prior entry analyses linked in the "历史入场分析" section. Tell the user what you found.

If `wiki/tickers/$ARGUMENTS/` does not exist at all, warn: "No existing research found for $ARGUMENTS. Consider running `/stock-analyze $ARGUMENTS` first for a complete thesis. Proceeding with entry analysis only."

### 2. Technical position (SEPA)

Use the `sepa-strategy` skill to determine:
- Current Stage (1 / 2 / 3 / 4)
- Trend template score (X/7 criteria passing)
- Price vs 50MA / 150MA / 200MA (exact values)
- ATR (14-day Average True Range)
- Current pattern if any (VCP, flat base, cup-with-handle, bull flag, none)
- Pivot point / ideal entry price
- Whether current setup is Actionable / Watch / Not Ready

### 3. Current price and volume

Use the `yfinance-data` skill to get:
- Current price (or last close)
- Today's volume vs 50-day average volume (volume ratio)
- 52-week high and low
- Distance from 52-week high (%)

### 4. Liquidity check

Use the `stock-liquidity` skill to estimate:
- ADTV (average daily dollar volume)
- Estimated slippage for a $25K position

### 5. Option market levels

Query the unusual_whales Telegram bot (Chat ID: 5241900942) using tdl:

```bash
tdl chat export -c 5241900942 -T last -i 5 --all --with-content -o ~/tdl-exports/uw_entry.json
```

Then send `/max_pain $ARGUMENTS` to the bot via Telegram app manually if needed and note the response. Report:
- Max pain strike for the nearest expiry
- Nearest OI wall above current price (resistance)
- Nearest OI wall below current price (support)

If the bot data is unavailable, note "OI data unavailable" and continue.

### 6. Options payoff visualization (optional)

If the user has mentioned an options strategy (calls, puts, spreads), use the `options-payoff` skill to visualize the P&L curve.

Skip this step if the user only wants stock entry analysis.

### 7. Synthesize and present entry plan

Present this structured output for user confirmation:

```
## Entry Analysis — $ARGUMENTS — [DATE]

**Current Price:** $XX.XX
**Technical Stage:** Stage X ([description])
**Setup Quality:** [Actionable / Watch / Not Ready]
**Pattern:** [VCP / flat base / none / etc.]

### Entry Plan
入场区间：$XX.XX — $XX.XX
（理由：[1 sentence — why this zone, e.g. "pivot breakout above $XX.XX with volume confirmation"]）

止损位：$XX.XX（风险：X% from entry midpoint）
（理由：[1 sentence — e.g. "below 50MA at $XX.XX"]）

目标价 1：$XX.XX（盈亏比 X:1，理由：[prior resistance / measured move / etc.]）
目标价 2：$XX.XX（盈亏比 X:1，理由：[52-week high / analyst target / etc.]）

### Position Sizing
基于 1% 本金风险：
- $50K 组合 → 最大仓位 $X,XXX（约 XXX 股）
- $100K 组合 → 最大仓位 $X,XXX（约 XXX 股）
- $200K 组合 → 最大仓位 $X,XXX（约 XXX 股）

### Key Levels
ATR (14d)：$X.XX
52周高：$XX.XX（距今 X%）
52周低：$XX.XX
期权 Max Pain：$XX（[到期日]）
OI 阻力位：$XX.XX
OI 支撑位：$XX.XX

### Execution Note
ADTV：$XXM — [Large/Mid/Small] cap liquidity
预计滑点（$25K 仓位）：约 $XX
```

Ask user: "确认写入文件？"

### 8. Write entry file

After user confirmation, write `wiki/tickers/$ARGUMENTS/entry-[TODAY'S DATE].md`:

```markdown
# $ARGUMENTS — Entry Analysis · [DATE]

**Generated by:** `/stock-entry $ARGUMENTS`
**Date:** [TODAY'S DATE]

## Entry Plan

入场区间：$XX.XX — $XX.XX
止损位：$XX.XX（风险：X%）
目标价 1：$XX.XX（盈亏比 X:1）
目标价 2：$XX.XX（盈亏比 X:1）

## Position Sizing（基于 1% 本金风险）

| 组合规模 | 最大仓位 | 股数 |
|---------|---------|------|
| $50K | $X,XXX | XXX |
| $100K | $X,XXX | XXX |
| $200K | $X,XXX | XXX |

## Technical Context

**Stage:** X | **Setup:** [description] | **Pattern:** [pattern or none]
**ATR (14d):** $X.XX
**Price vs MAs:** [above/below 50MA / 150MA / 200MA]

## Key Levels

| Level | Price |
|-------|-------|
| 52周高 | $XX.XX |
| 52周低 | $XX.XX |
| 期权 Max Pain | $XX.XX |
| OI 阻力 | $XX.XX |
| OI 支撑 | $XX.XX |

## Execution

ADTV: $XXM | 预计滑点: ~$XX
```

### 9. Update changelog

Append to `wiki/tickers/$ARGUMENTS/changelog.md` (newest-on-top, below the header, before existing entries):

```markdown
## [TODAY'S DATE] — Entry Analysis

**入场区间：** $XX.XX — $XX.XX | **止损：** $XX.XX（X%）| **目标 1：** $XX.XX | **目标 2：** $XX.XX
**Setup：** Stage X，[pattern]
**File：** [entry-TODAY'S DATE.md](entry-[TODAY'S DATE].md)

---
```

### 10. Update overview

Read `wiki/tickers/$ARGUMENTS/overview.md`. Find or create a section called `## 历史入场分析`. Add a link at the top of that section's list:

```markdown
## 历史入场分析

- [TODAY'S DATE — 入场 $XX.XX–$XX.XX，止损 $XX.XX](entry-[TODAY'S DATE].md)
```

If the section already has entries, prepend the new link (newest first).

### 11. Confirm completion

Report: "入场分析完成：
- `wiki/tickers/$ARGUMENTS/entry-[DATE].md` 已创建
- `changelog.md` 已更新
- `overview.md` 已添加链接"
```

- [ ] **Step 2: Smoke test with POET**

Run `/stock-entry POET` and verify:
- Steps 2–5 run and produce real data
- Structured entry plan is presented
- After confirmation, `wiki/tickers/POET/entry-[today].md` is created
- `wiki/tickers/POET/changelog.md` has a new entry appended
- `wiki/tickers/POET/overview.md` has a "历史入场分析" section with a link

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/stock-entry.md
git commit -m "feat: add /stock-entry command with changelog and overview linkback"
```

---

## Task 3: `/chen-integrate` command

**Files:**
- Create: `.claude/commands/chen-integrate.md`
- Created by command: `wiki/opinions/chen-yun-log/YYYY-MM-DD.md`

- [ ] **Step 1: Understand the existing chen-yun-log format**

Read `wiki/opinions/chen-yun-log/2026-04-24.md` to confirm the current format. The command must produce files that match this structure, plus add the validation table at the bottom.

- [ ] **Step 2: Write the command file**

Create `.claude/commands/chen-integrate.md` with this exact content:

```markdown
# chen-integrate

Parse the latest content from `raw/analyses/chen.md`, write a structured daily log entry under `wiki/opinions/chen-yun-log/`, and flag tickers that warrant social validation.

## Arguments

None. Always processes the latest content in `raw/analyses/chen.md`.

## Steps

### 1. Read the raw input

Read `raw/analyses/chen.md` in full.

### 2. Find the most recent processed date

List all files in `wiki/opinions/chen-yun-log/` and find the most recent date (YYYY-MM-DD filename). Read that file to understand the last processed content.

If no log files exist, treat everything in `raw/analyses/chen.md` as new.

### 3. Identify new content

Compare `raw/analyses/chen.md` against the last log entry. Identify content that has not yet been written to a log file — typically new dated sections or entries after the last processed date.

Ask the user: "最新日志到 [last date]。将处理 [new date] 的内容，是否继续？"

### 4. Extract ticker mentions

For the new content, extract each ticker mention with:
- Ticker symbol (e.g. ATOM, WOLF, POET)
- Recommendation strength: count the 🔥 emoji (🔥 = mild, 🔥🔥 = moderate, 🔥🔥🔥 = strong)
- Chen's exact words (quote in Chinese)
- Observation type: 首次推荐 / 加仓 / 持有 / 止损 / 观望

To determine "首次推荐": check if the ticker appears in any prior log file in `wiki/opinions/chen-yun-log/`. If not found, it is a first mention.

To determine "连续提及 N 日": scan the last 7 log files for this ticker. Count consecutive days with mentions.

### 5. Write the daily log file

Write `wiki/opinions/chen-yun-log/[NEW DATE].md` with this structure:

```markdown
# Chen-Yun 日志 — [DATE]（[weekday]）

> [← 返回索引](../chen-yun.md)

[For each ticker, one bullet:]
- **[TICKER]** [——首次推荐 if applicable] [🔥 count]："[Chen's exact words]"[；brief context if needed]

---

## 建议社交验证

[If no tickers meet the threshold, write: "本日无需优先验证的 ticker。"]

| Ticker | 原因 | 状态 |
|--------|------|------|
[For each ticker meeting threshold:]
| [TICKER] | [首次推荐，🔥🔥🔥 / 连续 N 日提及 / 强推] | 待验证 |
```

**Validation threshold (include if ANY condition is true):**
- First-time mention
- 🔥🔥🔥 rating
- Mentioned ≥3 consecutive days

### 6. Present the validation list to user

Display the "建议社交验证" table and ask for each flagged ticker:

"以下 ticker 建议运行 `/chen-validate`：
[list]

逐个确认是否执行验证，或输入 'skip' 跳过全部。"

Wait for user response. Do not auto-execute validation.

### 7. Confirm completion

Report: "Chen 日志已写入：`wiki/opinions/chen-yun-log/[DATE].md`
[N] 个 ticker 待验证：[list]"
```

- [ ] **Step 3: Smoke test**

Run `/chen-integrate`. Verify:
- The command correctly identifies the last processed date
- New content is extracted from `raw/analyses/chen.md`
- Log file is written with correct format matching `2026-04-24.md`
- Validation table is present at the bottom
- User is prompted for each flagged ticker

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/chen-integrate.md
git commit -m "feat: add /chen-integrate command with validation flagging"
```

---

## Task 4: `/chen-validate` command

**Files:**
- Create: `.claude/commands/chen-validate.md`
- Modified by command: `wiki/opinions/chen-yun-log/YYYY-MM-DD.md` (validation results appended)

- [ ] **Step 1: Write the command file**

Create `.claude/commands/chen-validate.md` with this exact content:

```markdown
# chen-validate

Cross-validate a ticker that Yun Chen has pushed, using social sentiment, options flow, and technical data. Writes results back to the most recent chen-yun-log that contains this ticker.

## Arguments

Required: `<TICKER>` — the stock symbol to validate (e.g. `ATOM`, `WOLF`).

## Steps

### 1. Find Chen's opinion for this ticker

Read the most recent `wiki/opinions/chen-yun-log/` file that contains `$ARGUMENTS`. Extract Chen's exact words and recommendation strength for context.

If no log file mentions `$ARGUMENTS`, warn: "未找到 $ARGUMENTS 的 Chen 记录。请先运行 `/chen-integrate`。" and stop.

### 2. Twitter/X sentiment

Use the `twitter-reader` skill to search: `"$ARGUMENTS"` with `--filter live --limit 20`.

Summarize:
- Sentiment: 偏多 / 中性 / 偏空
- Discussion volume: 高 (>15 results) / 中 (5–15) / 低 (<5)
- Key themes in the tweets (1–2 sentences)

### 3. Cross-platform social sentiment

Use the `finance-sentiment` skill for `$ARGUMENTS`.

Extract:
- Reddit mention count and sentiment score
- X.com mention count and sentiment score
- News sentiment score
- Overall signal: Bullish / Neutral / Bearish

### 4. Recent price and volume

Use the `yfinance-data` skill to get:
- Price change over last 5 trading days (%)
- Volume ratio (today vs 50-day average)
- Whether the stock is above or below its 20MA and 50MA

Summarize: 突破 / 盘整 / 回调 / 下跌

### 5. Options flow check

Query the unusual_whales Telegram bot (Chat ID: 5241900942):

```bash
tdl chat export -c 5241900942 -T last -i 3 --all --with-content -o ~/tdl-exports/uw_validate.json
```

In the Telegram app, send `/darkpool_ticker $ARGUMENTS` and `/flow_alerts $ARGUMENTS` to the bot. Note the response.

Classify: 异常（大宗看涨）/ 异常（大宗看跌）/ 正常

If bot is unavailable, note "期权流数据不可用" and continue.

### 6. Analyst estimate direction

Use the `estimate-analysis` skill for `$ARGUMENTS`.

Extract the 90-day estimate revision direction: 上调 / 持平 / 下调

### 7. Synthesize

Produce this structured summary:

```
## $ARGUMENTS 验证 — [DATE]

**Chen 观点：** [quote from step 1, strength 🔥]

| 维度 | 信号 | 详情 |
|------|------|------|
| Twitter 情绪 | [偏多/中性/偏空] | 讨论量[高/中/低]，[key theme] |
| 跨平台情绪 | [Bullish/Neutral/Bearish] | Reddit: [score], X: [score] |
| 近期量价 | [突破/盘整/回调/下跌] | [X]d 涨跌 [%], 量比 [X] |
| 期权流 | [异常/正常] | [大宗看涨/看跌 or 正常] |
| 分析师预期 | [上调/持平/下调] | 90 日修正方向 |

**综合评估：** 配合 / 背离 / 中性
**建议：** [可进一步研究 / 谨慎 / 暂时观望]
```

### 8. Write results back to the log

Find the most recent `wiki/opinions/chen-yun-log/` file containing `$ARGUMENTS`. Update the validation table row for `$ARGUMENTS`:

Change `| [TICKER] | [reason] | 待验证 |` to `| [TICKER] | [reason] | ✅ 已验证 | [综合评估 + 1-line summary] |`

Append the full validation detail block after the table:

```markdown
### [TICKER] 验证详情 · [DATE]

| 维度 | 信号 | 详情 |
...（full table from step 7）

**综合评估：** [配合/背离/中性]
**建议：** [可进一步研究 / 谨慎 / 暂时观望]
```

### 9. Prompt for deeper analysis

Ask the user:

"验证完成。综合评估：[result]。
是否进一步运行 `/stock-analyze $ARGUMENTS` 做完整个股研究？"

Wait for user response. Do not auto-execute.

### 10. Confirm completion

Report: "$ARGUMENTS 验证已写回：`wiki/opinions/chen-yun-log/[DATE].md`"
```

- [ ] **Step 2: Smoke test with ATOM**

ATOM was flagged as a first-time 🔥🔥🔥 recommend in the 2026-04-24 log. Run `/chen-validate ATOM` and verify:
- Step 1 finds the 2026-04-24.md log and extracts Chen's quote
- Steps 2–6 run and produce real data
- Step 7 produces the validation table
- Step 8 updates `wiki/opinions/chen-yun-log/2026-04-24.md` — the ATOM row changes from "待验证" to "✅ 已验证"
- Step 9 prompts for `/stock-analyze ATOM`

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/chen-validate.md
git commit -m "feat: add /chen-validate command with log writeback and stock-analyze prompt"
```

---

## Self-Review

**Spec coverage check:**
- F1 `/stock-analyze`: ✅ Task 1 — all 8 data sources, 15 sections A–O, output files, zh translations
- F2 `/stock-entry`: ✅ Task 2 — entry/stop/targets, position sizing, OI levels, entry file, changelog append, overview link
- F3 `/chen-integrate`: ✅ Task 3 — raw parse, last-date detection, ticker extraction, log write, validation table
- F4 `/chen-validate`: ✅ Task 4 — 5 data sources, validation table, log writeback, stock-analyze prompt

**Placeholder scan:** None found. All steps contain concrete content, exact file paths, and real command syntax.

**Type consistency:** `$ARGUMENTS` used consistently across all command files for ticker argument. File paths use exact `wiki/` structure throughout. Telegram bot ID `5241900942` consistent across Tasks 2 and 4.
