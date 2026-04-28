# morning-check

Bridge EOD planning and next-day execution decisions. Compares live price to existing entry plan or generates one on the fly. Handles both new entry candidates and existing positions.

If `<TICKER>` is `ALL`, run batch scan over all active positions.

## Arguments

Required: `<TICKER>` — uppercase ticker symbol (e.g. `POET`, `INTT`) or literal `ALL` for batch mode.

Optional flags:
- `--need-cash` — bias decision toward Trim/Exit
- `--need-cash-urgent` — strongly bias toward Exit (any positive P&L → Trim 50%)
- `--confirm` — confirm a just-executed trade and update positions.md

## Steps

### 1. Normalize and detect mode

Normalize ticker to uppercase. If equal to `ALL`, jump to **Section 1.5 ALL Mode** below. Otherwise continue with single-ticker deep mode (Steps 2–8).

### 1.5 ALL Mode (batch scan)

Read all active positions:

```bash
py scripts/positions.py list --status Active
```

For each ticker returned, run a simplified version of Steps 3–5 (skip Step 2 entry plan check; skip Steps 6–7 user confirmation and file updates).

For each position, run inline Python to fetch live data:

```bash
py - <<'EOF'
import sys, yfinance as yf, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
TICKERS = ["POET", "INTT", "..."]  # populate from positions.list output
for tk in TICKERS:
    t = yf.Ticker(tk)
    h = t.history(period="3mo", interval="1d")
    h_5m = t.history(period="1d", interval="5m")
    price = h["Close"].iloc[-1]
    prev = h["Close"].iloc[-2]
    open_p = h_5m["Open"].iloc[0] if len(h_5m) else price
    gap = (open_p / prev - 1) * 100
    ma50 = h["Close"].rolling(50).mean().iloc[-1]
    atr = (h["High"] - h["Low"]).rolling(14).mean().iloc[-1]
    print(json.dumps({"ticker": tk, "price": float(price), "gap": float(gap),
                      "ma50": float(ma50), "atr": float(atr)}))
EOF
```

Apply persona's **持仓决策矩阵** to each ticker (see Section 5 below). Then output a summary:

```
## /morning-check ALL — YYYY-MM-DD HH:MM ET

**持仓 N 只：** [ticker list]

| Ticker | Shares | Cost | 现价 | P&L% | Stop | 矩阵 | 推荐 | 关键提示 |
|--------|--------|------|------|------|------|------|------|---------|
| ...    | ...    | ...  | ...  | ...  | ...  | ...  | ...  | ...     |

### 行动摘要
- 🛑 N 个 Exit 信号：[list]
- ⚠️ N 个 Trim/调整止损：[list]
- ✅ N 个 Hold 不变：[list]

### 整体上下文
- SPY ±X%, QQQ ±X%（[判断]）
- 组合总成本：$X,XXX, 当前总值：$X,XXX
- 今日浮盈：±$XXX（±X%）

**深度查看：** 调用 `/morning-check <TICKER>` 查看完整决策矩阵
```

ALL mode ends here. Skip the rest (no user confirmation, no positions.md updates).

### 2. Check existing position

```bash
py scripts/positions.py read --ticker $TICKER
```

Capture JSON output:
- Non-null → position exists, will use **持仓决策矩阵** (Section 5.B)
- `null` → no position, will use **新仓决策矩阵** (Section 5.A)

### 3. Check yesterday's entry plan

Find the most recent file matching `wiki/tickers/$TICKER/entry-*.md` (sort filenames alphabetically descending; `YYYY-MM-DD` filenames sort chronologically). Read the file. Extract:
- Entry zone (low / high)
- Stop price
- Target 1 / Target 2
- ATR (14d) if listed
- Trigger conditions

If no entry-*.md exists → mark as "**无昨日计划，进入生成模式**" and proceed.

### 4. Fetch live data

Run inline Python to fetch via yfinance:

```bash
py - <<'EOF'
import yfinance as yf
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

t = yf.Ticker("$TICKER")
info = t.info
hist = t.history(period="3mo", interval="1d")
hist_5m = t.history(period="1d", interval="5m")

price = info.get("currentPrice", hist["Close"].iloc[-1])
prev_close = hist["Close"].iloc[-2]
today_open = hist_5m["Open"].iloc[0] if len(hist_5m) else price
gap_pct = (today_open / prev_close - 1) * 100
ma50 = hist["Close"].rolling(50).mean().iloc[-1]
ma150 = hist["Close"].rolling(150).mean().iloc[-1] if len(hist) >= 150 else None
ma200 = hist["Close"].rolling(200).mean().iloc[-1] if len(hist) >= 200 else None
atr = (hist["High"] - hist["Low"]).rolling(14).mean().iloc[-1]
vol_5m = hist_5m["Volume"].sum() if len(hist_5m) else 0
vol_20d_avg = hist["Volume"].rolling(20).mean().iloc[-1]
# 78 5-min bars in a typical regular session
vol_ratio_5m = vol_5m / (vol_20d_avg / 78) if vol_20d_avg else 0

print(f"price=${price:.2f}")
print(f"prev_close=${prev_close:.2f}")
print(f"today_open=${today_open:.2f}")
print(f"gap_pct={gap_pct:+.2f}%")
print(f"ma50=${ma50:.2f}")
print(f"ma150=${ma150:.2f}" if ma150 else "ma150=N/A")
print(f"ma200=${ma200:.2f}" if ma200 else "ma200=N/A")
print(f"atr=${atr:.2f}")
print(f"vol_5m_ratio={vol_ratio_5m:.2f}x")
EOF
```

Also fetch SPY and QQQ for market context:

```bash
py - <<'EOF'
import yfinance as yf
for tk in ["SPY", "QQQ"]:
    t = yf.Ticker(tk)
    h = t.history(period="2d")
    pct = (h["Close"].iloc[-1] / h["Close"].iloc[-2] - 1) * 100
    print(f"{tk}_gap={pct:+.2f}%")
EOF
```

Optionally check the ticker's recent changelog for论点 weakened/broken markers:

```bash
grep -i "weakened\|broken\|论点 weakened\|论点 broken" wiki/tickers/$TICKER/changelog.md 2>/dev/null | head -3
```

### 5. Apply decision matrix

#### A. 新仓决策矩阵（无持仓）

| 当前价 vs 入场区间 | 推荐动作 |
|-------------------|---------|
| 区间内（zone ± 0.5×ATR）| ✅ Execute（按计划，限价单挂中点）|
| 区间下方，未到止损 | ⏳ Wait（等回升或回测止损反弹）|
| 触及/跌破止损 | 🛑 Cancel（趋势已破，重写 entry-*.md）|
| 区间上方 < 1 ATR | ⚠️ Chase 50%（半仓追，止损调至 entry mid 下 1 ATR）|
| 区间上方 > 1 ATR | ⛔ Skip（已扩展，等下次盘整）|

无昨日计划时（生成模式）：
- 入场区间 = 50MA ± 0.5 ATR
- 止损 = 50MA - 1.5 ATR
- 目标 1 = 50MA + 2 ATR；目标 2 = 50MA + 4 ATR
- 仅当价格当前在 50MA 之上 + 趋势模板 ≥5/8 时建议 Execute

#### B. 持仓决策矩阵

| 当前 P&L | 信号 | 推荐 |
|---------|------|------|
| > +20% | Stage 2 健康 | Hold + 上调止损至 BE 或最近 swing low |
| > +20% | Stage 3 / 抛物线 / 跌破 50MA | Trim 50%，剩余移动止损 |
| -8% < P&L < +20% | 区间震荡 | Hold + 维持原止损 |
| 触及/跌破止损 | 任何 | 🛑 Exit 全部 |
| 单日 gap +30% | 抛物线顶 | Trim 50% 锁利 |
| 单日 gap -30% | 重大利空 | 重新评估（论点是否破？破→Exit；未破→Hold 缩仓）|
| 接近目标 1（±0.5×ATR）| 任何 | Trim 25-33%，移动止损至 BE |
| 突破目标 2 | 强势 | Trim 25%，剩余 trailing stop |

#### C. 叠加规则

- SPY/QQQ 同步 gap > ±1% → 新仓动作降一级（Execute → Chase 50%；Chase → Wait）
- 5min 量比 < 0.5x → 标"低信号"，Wait 优先
- 5min 量比 > 3x → 标"催化剂存在"，提示用户检查新闻
- 该 ticker 最近 changelog 含 "weakened/broken" → 持仓 Trim 阈值降一级
- `--need-cash` → 整体 Trim/Exit 倾向加强（持仓矩阵中的 Hold 改为 Trim 25%）
- `--need-cash-urgent` → 任何持仓 P&L 正向都倾向 Trim 50%

### 6. Output decision report

Format:

```
## /morning-check $TICKER — YYYY-MM-DD HH:MM ET

**持仓状态：** [Active N 股 @ $X.XX, 入场 YYYY-MM-DD, 止损 $X.XX] OR [无持仓]
**昨日计划：** [entry-YYYY-MM-DD.md 摘要] OR [无昨日计划，生成模式]
**当前价：** $X.XX [vs 成本 $Y.YY (P&L%)] OR [vs 入场区间 $A-$B]

### 实时上下文
- 今日 gap: ±X% (vs $prev_close 收盘)
- 5min 量比: X×（[配合/低/异常]）
- SPY gap: ±X%, QQQ gap: ±X% （[平稳/系统性 risk-on/-off]）
- ATR(14d): $X.XX
- MA: 50MA $X (above/below), 150MA $X, 200MA $X
- 论点变化（changelog）: [若有 weakened/broken 标记，列出]

### 决策矩阵应用
[根据上下文匹配矩阵规则，引用具体行]
[叠加规则触发的，列出每条调整]

### 推荐动作
[✅ Execute / ⏳ Wait / 🛑 Cancel / ⚠️ Chase 50% / ⛔ Skip / Hold / Trim X% / Exit]
[具体执行参数：限价/市价、价位、股数]

### 替代方案
[如不执行，下次什么条件再考虑]

### 是否执行？
[ ] 选项 1（推荐动作）
[ ] 选项 2（替代）
[ ] Hold/Skip
[ ] Other：____
```

Wait for user explicit confirmation.

### 7. Update positions.md (if applicable)

Based on user's choice:

**新仓 Execute：**
Ask user for fills (price, shares). Then run:
```bash
py scripts/positions.py add --ticker $TICKER --shares <N> --avg-cost <P> \
  --entry-date $TODAY --stop <S> --target1 <T1> --target2 <T2> \
  --notes "From entry-YYYY-MM-DD"
```

**Trim：**
Ask for shares trimmed and exit price. Update remaining shares + status:
```bash
py scripts/positions.py update --ticker $TICKER --shares <new_count> \
  --status Trimmed --notes "Trimmed N shares @ $P on $TODAY"
```

**Exit 全部：**
```bash
py scripts/positions.py close --ticker $TICKER --avg-exit <P> \
  --reason "<reason>" --closed-date $TODAY
```

**调整止损：**
```bash
py scripts/positions.py update --ticker $TICKER --stop <new_stop> \
  --notes "Stop adjusted on $TODAY: <reason>"
```

**Skip / Wait / Hold：** 不更新 positions.md。

### 8. Confirm completion

Report final state:

```
✅ 决策记录完成：
- 推荐动作：[action]
- 用户确认：[chose]
- positions.md 已更新（[操作]）/ 未更新
```
