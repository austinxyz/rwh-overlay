# chen-integrate

Parse the latest content from `raw/analyses/chen.md`, write a structured daily log entry under `wiki/opinions/chen-yun-log/`, and flag tickers that warrant social validation.

## Arguments

None. Always processes the latest content in `raw/analyses/chen.md`.

## Steps

### 1. Read the raw input

Read `raw/analyses/chen.md` in full.

### 2. Find the most recent processed date

List all files in `wiki/opinions/chen-yun-log/` using glob pattern `wiki/opinions/chen-yun-log/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md`. Sort file paths alphabetically descending (YYYY-MM-DD filenames are chronological when sorted alphabetically — do NOT sort by file modification time) to find the most recent date. Read that file to understand the last processed content.

If no log files exist, treat all content in `raw/analyses/chen.md` as new.

### 3. Identify new content

Compare `raw/analyses/chen.md` against the last log entry. Identify content that has not yet been written to a log file. Detection rule: look for date markers in `raw/analyses/chen.md` (lines that start with `##` followed by a date, or clear date section headers like `#### YYYY-MM-DD` or `**YYYY年MM月DD日**`). Any date section in the raw file with a date AFTER the last log filename date is considered new content.

Ask the user: "最新日志到 [last date in YYYY-MM-DD format]。将处理 [new date] 的内容，是否继续？" Wait for an affirmative reply (e.g., "yes", "好", "继续") before proceeding. If there is no new content, report "raw/analyses/chen.md 无新内容（上次处理至 [date]）" and stop.

### 4. Extract ticker mentions

For the new content, extract each ticker mention with:
- Ticker symbol in uppercase (e.g., ATOM, WOLF, POET)
- Recommendation strength: count the 🔥 emoji (🔥 = mild, 🔥🔥 = moderate, 🔥🔥🔥 = strong)
- Chen's exact words in Chinese (quote directly)
- Observation type: 首次推荐 / 加仓 / 持有 / 止损 / 观望

To determine "首次推荐": check all existing log files in `wiki/opinions/chen-yun-log/` for the ticker symbol. If not found in any file, it is a first mention — mark with "——首次推荐" in the bullet.

To determine consecutive days: scan the 7 most recent log files for the ticker symbol. Count how many consecutive days it appears ending with today's new date.

### 5. Write the daily log file

Write `wiki/opinions/chen-yun-log/[NEW DATE IN YYYY-MM-DD FORMAT].md` with this structure:

```markdown
# Chen-Yun 日志 — [DATE]（[weekday in Chinese: 周一/周二/周三/周四/周五/周六/周日]）

> [← 返回索引](../chen-yun.md)

[One bullet per ticker, using this format:]
- **[TICKER][——首次推荐 if applicable]** [🔥 emoji count if any]："[Chen's exact words]"[；additional context if needed]

---

## 建议社交验证

[If NO tickers meet the validation threshold:]
本日无需优先验证的 ticker。

[If tickers DO meet the threshold, use this table:]
| Ticker | 原因 | 状态 |
|--------|------|------|
| [TICKER] | [首次推荐，🔥🔥🔥 / 连续 N 日提及 / 强推] | 待验证 |
```

**Validation threshold — include a ticker if ANY of these are true:**
- First-time mention in any log file
- 🔥🔥🔥 rating (3 fire emojis)
- Mentioned in ≥3 consecutive days (including today's new entry)

### 6. Present the validation list

Display the "建议社交验证" section to the user and say:

"以下 ticker 建议运行 `/chen-validate`：[list]

逐个确认是否执行验证，或输入 'skip' 跳过全部。"

Wait for user response. Do not auto-execute `/chen-validate`.

If no tickers met the threshold, skip this step and go directly to Step 7.

### 7. Update `wiki/opinions/chen-yun.md`

Read `wiki/opinions/chen-yun.md`. Make the following three changes in order:

**7a — Update header metadata (top of file):**
Find the two lines:
```
> **捕获日期范围**: YYYY-MM-DD → [old date]
> **最后导入**: [old date]
```
Replace `[old date]` in both lines with the new date being processed (YYYY-MM-DD format).

**7b — Prepend new row(s) to the 时间线日志 table:**
Find the table that starts with `| 日期 | 周几 | 关键标的 / 事件 |`. Insert one new row per new date processed, immediately after the header rows (`| --- |` separator line), newest date first. Row format:
```
| [YYYY-MM-DD](chen-yun-log/YYYY-MM-DD.md) | [weekday] | [2–4 key ticker/event highlights from that day's log] |
```
Highlights should name tickers with first-push (首推), validated (✅), or thematically notable events. Keep each cell under 80 characters.

**7c — Add new tickers to 股票索引 table:**
Find the table that starts with `| 股票 | 赛道 | 首次提及 | 他的描述 / 价格信号 |`. For each ticker that is a **首次推荐** in today's log (i.e., first appearance across all log files), prepend a new row at the top of the table:
```
| [TICKER] | [lane/sector] | [date] | [Chen's description + any validation result if already done] |
```
Also update any existing ticker rows where today's log adds material new information (e.g., a price validation, a 复盘 confirmation, a thesis change).

Do NOT re-add tickers that already have rows in the 股票索引.

### 8. Confirm completion

Report: "Chen 日志已写入：`wiki/opinions/chen-yun-log/[DATE].md`
chen-yun.md 已同步更新（元数据 + 时间线 + 股票索引）
[N] 个 ticker 待验证：[comma-separated list, or '无' if none]"
