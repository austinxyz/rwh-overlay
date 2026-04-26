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

### 7. Confirm completion

Report: "Chen 日志已写入：`wiki/opinions/chen-yun-log/[DATE].md`
[N] 个 ticker 待验证：[comma-separated list, or '无' if none]"
