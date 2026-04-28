# chen-validate

Cross-validate a ticker that Yun Chen has pushed, using social sentiment, options flow, and technical data. Writes results back to the most recent chen-yun-log that mentions this ticker.

## Arguments

Required: `<TICKER>` — the stock symbol to validate (e.g. `ATOM`, `WOLF`).

## Steps

### 1. Normalize and find Chen's opinion

Normalize `$ARGUMENTS` to uppercase.

Search all files in `wiki/opinions/chen-yun-log/` for the ticker symbol `$ARGUMENTS`. Find the most recent log file (sort filenames alphabetically descending — YYYY-MM-DD names are chronological when sorted alphabetically, do NOT sort by modification time) that contains `$ARGUMENTS`. Read that file and extract:
- Chen's exact words about `$ARGUMENTS`
- Recommendation strength (count 🔥 emojis)

If no log file mentions `$ARGUMENTS`, report: "未找到 $ARGUMENTS 的 Chen 记录。请先运行 `/chen-integrate`。" and stop.

### 2. Twitter/X sentiment

Use the `twitter-reader` skill to search for `"$ARGUMENTS"` with `--filter live --limit 20`.

Summarize:
- Sentiment: 偏多 / 中性 / 偏空
- Discussion volume: 高 (>15 results) / 中 (5–15) / 低 (<5)
- Key themes in 1–2 sentences

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
- Volume ratio: today's volume vs 50-day average
- Whether the stock is above or below its 20MA and 50MA

Summarize as one of: 突破 / 盘整 / 回调 / 下跌

### 5. Options flow check

Query the unusual_whales Telegram bot (Chat ID: 5241900942):

```bash
tdl chat export -c 5241900942 -T last -i 5 --all --with-content -o ~/tdl-exports/uw_validate.json
py scripts/read_uw_bot.py --path ~/tdl-exports/uw_validate.json --ticker $ARGUMENTS --limit 5
py scripts/read_uw_bot.py --path ~/tdl-exports/uw_validate.json --section flow --limit 5
```

Look for any references to `$ARGUMENTS` in the helper output. Note: the user can also manually send `/darkpool_ticker $ARGUMENTS` and `/flow_alerts $ARGUMENTS` to the bot in the Telegram app for fresher data.

Classify: 异常（大宗看涨）/ 异常（大宗看跌）/ 正常

If the bot data is unavailable or contains no data for `$ARGUMENTS`, classify as "期权流数据不可用" and continue.

### 6. Analyst estimate direction

Use the `estimate-analysis` skill for `$ARGUMENTS`.

Extract the 90-day estimate revision direction: 上调 / 持平 / 下调

If `$ARGUMENTS` has insufficient analyst coverage (no estimates available), note "分析师覆盖不足" and continue.

### 7. Synthesize and present

Present this structured summary to the user:

```
## $ARGUMENTS 验证 — [TODAY'S DATE IN YYYY-MM-DD]

**Chen 观点：** "[Chen's exact words]" [🔥 count]

| 维度 | 信号 | 详情 |
|------|------|------|
| Twitter 情绪 | [偏多/中性/偏空] | 讨论量[高/中/低]；[key theme 1–2句] |
| 跨平台情绪 | [Bullish/Neutral/Bearish] | Reddit: [score/count], X: [score/count] |
| 近期量价 | [突破/盘整/回调/下跌] | 5d涨跌 [%], 量比 [X]x |
| 期权流 | [异常/正常/不可用] | [大宗看涨/看跌/正常/不可用] |
| 分析师预期 | [上调/持平/下调/不足] | 90日修正方向 |

**综合评估：** 配合 / 背离 / 中性
**建议：** 可进一步研究 / 谨慎 / 暂时观望
```

**Scoring logic for 综合评估:**
- **配合**: ≥3 of the 5 dimensions show positive signals (偏多, Bullish, 突破, 看涨, 上调)
- **背离**: ≥3 of the 5 dimensions show negative signals (偏空, Bearish, 下跌, 看跌, 下调)
- **中性**: anything else

Ask the user: "确认写回日志？" Wait for an explicit affirmative (e.g., 'yes', 'ok', '确认') before executing Step 8. If the user requests changes to the evaluation, revise and re-present Step 7.

### 8. Write results back to the log

Find the log file identified in Step 1. Make these two changes:

**Change 1 — Update the validation table row:**
Find the row: `| $ARGUMENTS | [reason] | 待验证 |`
Replace it with: `| $ARGUMENTS | [reason] | ✅ 已验证 | [综合评估] — [1-line summary] |`

Note: this adds a 4th column to that row only. The table header row also needs a 4th column added if it only has 3:
Change `| Ticker | 原因 | 状态 |` to `| Ticker | 原因 | 状态 | 综合评估 |`

**Change 2 — Append validation detail block after the table:**

```markdown
### $ARGUMENTS 验证详情 · [TODAY'S DATE IN YYYY-MM-DD]

| 维度 | 信号 | 详情 |
|------|------|------|
| Twitter 情绪 | [value] | [detail] |
| 跨平台情绪 | [value] | [detail] |
| 近期量价 | [value] | [detail] |
| 期权流 | [value] | [detail] |
| 分析师预期 | [value] | [detail] |

**综合评估：** [配合/背离/中性]
**建议：** [可进一步研究 / 谨慎 / 暂时观望]
```

If the row `| $ARGUMENTS | [reason] | 待验证 |` is not found (e.g., ticker was not flagged by `/chen-integrate`), append the detail block at the end of the file without modifying any table.

### 9. Prompt for deeper analysis

Ask the user:

"验证完成。综合评估：[result]。
是否进一步运行 `/stock-analyze $ARGUMENTS` 做完整个股研究？（yes/no）"

Wait for user response. Do not auto-execute `/stock-analyze`.

### 10. Confirm completion

Report: "$ARGUMENTS 验证已完成。结果已写回：`wiki/opinions/chen-yun-log/[filename].md`"
