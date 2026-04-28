# `/morning-check` 设计文档

**Date:** 2026-04-28
**Status:** Design — pending implementation plan
**Author:** austinxyz + Claude

---

## 1. 问题与目标

### 1.1 当前工作流的缺口

EOD（盘后）工作流已有：
- `/market-daily`：识别候选股票（潜力股区块、watchlist 异动）
- `/stock-entry`：为特定 ticker 写出具体入场计划（区间、止损、目标价）

但**次日开盘 30 分钟内**，价格往往已与昨日计划假设不符（gap up/down，盘前新闻，催化剂）。当前缺一个"开盘再确认"工具，导致：
- 候选股票的入场决策不能根据实时价格动态调整
- 已持仓的 trim/exit 决策（如 POET 4/27 -47% 崩盘）没有系统化判断框架
- 跨多只标的的决策需要人工逐个检查，不可扩展

### 1.2 目标

建立 **`/morning-check`** 命令，桥接 EOD 计划和开盘执行：
- 单 ticker 模式（深度）：1-2 分钟内给出 Buy / Skip / Wait / Trim / Hold / Exit 决策
- 批量 ALL 模式（速览）：全部持仓状态一览，1-2 分钟扫完
- 自动维护 `data/positions.md`（持仓记录，gitignored）

### 1.3 范围（明确不做的）

- **不接券商 API**（不实时拉真实持仓 / 自动下单）
- **不做 pre-market 数据集成**（pre-market 流动性差、价格不可靠）
- **不替代** `/stock-entry`（仍然是 EOD 写计划的工具，本工具只做开盘对照）

---

## 2. 用户决策参数（已确认）

| 参数 | 选择 | 影响 |
|------|------|------|
| 时间窗口 | B（开盘 30 分钟）+ C（盘中等稳定） | 命令任何时刻可调用，不限定开盘瞬间 |
| 主要触发关切 | A（gap-open 偏离入场区间） | 决策矩阵以"价格 vs 区间"为主轴 |
| 计划来源 | C（混合：有计划 + 仅候选两种）| 自动检测，分"对照模式"vs"生成模式" |
| 候选数量 | A（1-2 只精挑） | 默认深度模式，ALL 作为补充批量模式 |
| 持仓决策 | B（新仓 + 已持仓双向） | 矩阵分两套：新仓 vs 持仓 |
| 持仓追踪 | C（设计内建立 positions.md） | 本设计同步交付追踪机制 |
| 存储位置 | D（`data/positions.md`，gitignored）| 本地结构化但不上传公开仓库 |

---

## 3. 架构

### 3.1 文件清单

| 路径 | 类型 | 说明 |
|------|------|------|
| `.claude/commands/morning-check.md` | 新增 | 命令定义 |
| `scripts/positions.py` | 新增 | positions.md CRUD 助手（read/write/update/close） |
| `data/positions.md` | 新增（运行时生成）| 持仓追踪文件，gitignored |
| `.gitignore` | 修改 | 加入 `data/positions.md` |

### 3.2 与现有工具的关系

```
EOD（已有）：
  /market-daily   → 候选列表 + 异动 + 板块/情绪
  /stock-entry    → entry-YYYY-MM-DD.md（per-ticker 入场计划）
  /stock-refresh  → 论点更新（changelog 含 thesis-break 标记）
  /chen-validate  → Chen 推荐的多维交叉验证

开盘（新）：
  /morning-check <TICKER>  → 单 ticker 深度决策
  /morning-check ALL       → 批量持仓扫描

盘后回环：
  /market-daily 又开始下一轮
```

### 3.3 数据源

| 数据 | 来源 | 用途 |
|------|------|------|
| 实时价、open、gap%、5min 量 | yfinance | 决策核心输入 |
| SPY/QQQ gap | yfinance | 大盘 context（叠加规则）|
| 50MA / 150MA / 200MA / ATR(14d) | yfinance | 技术水位 |
| 入场计划（区间、止损、目标价）| `wiki/tickers/<TICKER>/entry-*.md` | 对照模式输入 |
| 持仓数据（成本、股数、止损）| `data/positions.md` | 持仓决策输入 |
| 论点状态（Active/Watch/Avoid）| `wiki/tickers/<TICKER>/overview.md` 头部 | 决策叠加规则 |
| 最近论点变化 | `wiki/tickers/<TICKER>/changelog.md` | 检测 weakened/broken 标记 |

---

## 4. 命令流程

### 4.1 单 ticker 模式（`/morning-check POET`）

**Step 1 — 检测持仓状态**
```bash
py scripts/positions.py read --ticker POET
# 返回：{shares, avg_cost, entry_date, stop, targets, status, notes} 或 null
```

**Step 2 — 检测昨日入场计划**
- 查找 `wiki/tickers/POET/entry-YYYY-MM-DD.md`（最近一份）
- 提取入场区间、止损、目标价、触发条件、ATR
- 若无 → 标记"无昨日计划，进入生成模式"

**Step 3 — 拉实时数据**
- 当前价、今日 open、gap%
- 5min 量比 / 20d 平均
- SPY/QQQ gap
- 最近 4 周 weekly close（Stage 判断）
- 50MA、150MA、200MA、ATR(14d)

**Step 4 — 分支决策**

```
若 positions[POET] 存在 → 持仓决策矩阵
若 positions[POET] 不存在 且 有昨日计划 → 对照模式 + 新仓决策矩阵
若 positions[POET] 不存在 且 无昨日计划 → 生成模式 + 新仓决策矩阵
```

**Step 5 — 输出决策报告**
- 状态摘要
- 实时价 vs 计划/当前 P&L
- 上下文（SPY gap、量能、相关新闻）
- 推荐动作 + 具体执行参数（限价、市价、股数）
- 替代方案

**Step 6 — 用户确认 → 可选更新 positions.md**
- 用户输入 "yes / executed / 已成交" 或 "skip" 等
- 若新建仓 → 询问 fills（成交价、股数）→ append positions.md
- 若 trim/exit → 询问 fills → 更新现有 row 或移到 Closed
- 若 skip/wait → 不动 positions.md

### 4.2 批量 ALL 模式（`/morning-check ALL`）

**流程：**
1. 读 `data/positions.md` → 所有 `Active` / `Trimmed` 状态标的
2. 对每只 ticker 跑简化版 Step 3-4（不写文件、不询问 fills）
3. 输出**简表 + 行动摘要**
4. 不更新 positions.md（用户需对单 ticker 调用 deep mode 再确认）

**输出格式：**

```
## /morning-check ALL — YYYY-MM-DD HH:MM ET

**持仓 N 只：** [tickers]

| Ticker | Shares | Cost | 现价 | P&L% | Stop | 矩阵 | 推荐 | 关键提示 |
|--------|--------|------|------|------|------|------|------|---------|

### 行动摘要
- 🛑 N 个 Exit 信号：[list]
- ⚠️ N 个 Trim/调整止损：[list]
- ✅ N 个 Hold 不变：[list]

### 整体上下文
- SPY/QQQ gap, 大盘判断
- 组合总值，今日浮盈

**深度查看：** 调用 `/morning-check <TICKER>` 查看单标的完整决策
```

### 4.3 命令变体

| 命令 | 用途 |
|------|------|
| `/morning-check <TICKER>` | 单 ticker 深度模式 |
| `/morning-check ALL` | 批量扫描所有持仓 |
| `/morning-check <TICKER> --need-cash` | 倾向 Trim/Exit（持仓决策叠加规则） |
| `/morning-check <TICKER> --confirm` | 确认刚执行的交易，更新 positions.md |

---

## 5. 决策矩阵

### 5.1 新仓决策矩阵（无持仓）

| 当前价 vs 入场区间 | 推荐动作 | 调整参数 |
|-------------------|---------|---------|
| 区间内（zone ± 0.5×ATR）| ✅ **Execute** | 限价单挂中点 |
| 区间下方，未到止损 | ⏳ **Wait** | 等回升至区间，或回测止损反弹后入 |
| 触及/跌破止损 | 🛑 **Cancel** | 趋势已破，重写 entry-*.md |
| 区间上方 < 1 ATR | ⚠️ **Chase 50%** | 半仓追，止损调整至 entry mid 下 1 ATR |
| 区间上方 > 1 ATR | ⛔ **Skip** | 已扩展，等下次盘整 |

### 5.2 持仓决策矩阵

| 当前 P&L | 趋势/价格信号 | 推荐动作 |
|---------|--------------|---------|
| > +20% 浮盈 | 仍 Stage 2 健康 | **Hold + 上调止损至 BE 或最近 swing low** |
| > +20% 浮盈 | Stage 3 / 抛物线 / 跌破 50MA | **Trim 50%，剩余移动止损** |
| -8% < P&L < +20% | 区间震荡 | **Hold + 维持原止损** |
| 触及/跌破止损 | 任何 | 🛑 **Exit 全部** |
| 单日 gap +30% | 抛物线顶部 | **Trim 50% 锁利** |
| 单日 gap -30% | 重大利空 | **重新评估**：核心论点是否破？破→Exit；未破→Hold 缩仓 |
| 接近目标 1（±2%） | 任何 | **Trim 25-33%，移动止损至 BE** |
| 突破目标 2 | 强势 | **Trim 25%，剩余 trailing stop 裸跑** |

### 5.3 叠加规则（应用于两种矩阵）

| 触发条件 | 调整 |
|---------|------|
| SPY/QQQ 同步 gap > ±1% | 新仓动作降一级（Execute → Chase 50%；Chase → Wait） |
| 5min 量比 < 0.5×（开盘量极低）| 标"低信号", Wait 优先 |
| 5min 量比 > 3×（异常放量）| 标"催化剂存在", 触发新闻检查 |
| 该 ticker 最近 changelog 标记"论点 weakened/broken" | 持仓矩阵 Trim 阈值降一级 |
| 该 ticker 最近 chen-validate 结果"背离" | 谨慎倾向 Trim |
| `--need-cash` 标记 | 整体 Trim/Exit 倾向加强 |

---

## 6. positions.md 格式

```markdown
# Active Positions

> Last updated: YYYY-MM-DD
> Maintained by `/morning-check`. Manual edits OK.

| Ticker | Shares | Avg Cost | Entry Date | Stop | Target 1 | Target 2 | Status | Notes |
|--------|--------|----------|------------|------|----------|----------|--------|-------|
| POET | 500 | $11.20 | 2026-04-15 | $9.50 | $14.00 | $18.00 | Active | 4/27 跌破止损未严格执行 |
| INTT | 200 | $14.50 | 2026-04-10 | $13.00 | $18.00 | $22.00 | Active | 接近目标 1 |

# Closed Positions

| Ticker | Shares | Entry | Exit | Avg Cost | Avg Exit | P&L $ | P&L % | Reason | Closed Date |
|--------|--------|-------|------|----------|----------|-------|-------|--------|-------------|
| WOLF | 200 | 2026-03-15 | 2026-04-20 | $25.50 | $32.00 | +$1,300 | +25.5% | Target 1 hit | 2026-04-20 |
```

**字段说明：**
- `Status`: `Active` / `Trimmed`（部分平仓）/ `Watching`（监控但未持仓）
- `Stop`: 由 `/morning-check` 推荐自动更新（需用户确认）
- `Notes`: 自由文本，记录论点变化或重要事件
- `Closed Positions` 不限行数（保留完整交易历史用于回顾分析）

---

## 7. `scripts/positions.py` 接口

```bash
# 读取单 ticker
py scripts/positions.py read --ticker POET
# → JSON: {shares, avg_cost, entry_date, stop, target1, target2, status, notes} or null

# 读取所有 active 持仓
py scripts/positions.py list --status Active
# → JSON: [{ticker, ...}, ...]

# 添加新仓
py scripts/positions.py add \
  --ticker POET --shares 500 --avg-cost 11.20 --entry-date 2026-04-15 \
  --stop 9.50 --target1 14.00 --target2 18.00 --notes "From entry-2026-04-15"

# 更新现有仓位（部分平仓 / 调整止损）
py scripts/positions.py update --ticker POET \
  --shares 250 --status Trimmed --stop 8.50 --notes "Trimmed 50% on 4/28"

# 平仓（移到 Closed Positions）
py scripts/positions.py close --ticker POET \
  --avg-exit 7.95 --reason "Stop broken" --closed-date 2026-04-28
```

---

## 8. 边界与扩展点

### 8.1 不在本设计内（但可能后续扩展）

- **税务计算**：Closed Positions 中 P&L 是名义值，不区分短期/长期资本利得
- **多账户支持**：不区分 IRA / Brokerage / 401k
- **多币种**：仅 USD
- **期权追踪**：仅股票，期权仓位需要单独设计

### 8.2 已知边界情况

| 情景 | 处理 |
|------|------|
| ticker 在 positions.md 但 wiki/tickers/<TICKER>/ 不存在 | 仍可决策（用 yfinance 实时数据），但不能引用论点状态，警告"建议补 stock-analyze" |
| 同一 ticker 多次部分加仓 | `Avg Cost` 加权平均；`Notes` 中追加加仓事件 |
| 用户手动改 positions.md 后命令读取 | 自动检测格式错误并提示，不强制覆盖 |
| ALL 模式下某只 ticker yfinance 拉数据失败 | 标"数据不可用"，跳过，继续其他标的 |
| 同日多次调用 `/morning-check` | 每次重新拉实时数据；positions.md 不会被无意覆盖（仅在用户明确确认时更新）|

---

## 9. 验证标准（实施完成后如何确认工作）

| 验证 | 方法 |
|------|------|
| 单 ticker 模式输出正确决策 | 用 POET（已知 4/27 -47% 崩盘）历史数据回测，预期输出"Exit" |
| ALL 模式批量扫描 | 创建 5 只测试持仓，运行 ALL，确认输出表格完整 |
| 对照模式 vs 生成模式 | 同一 ticker，删除 entry-*.md 后重跑，确认进入生成模式且仍输出合理决策 |
| positions.md CRUD | add → update → close 全流程，确认文件格式不损坏 |
| 叠加规则触发 | 模拟 SPY -1.5% gap 时调用，确认推荐降一级 |
| 编码处理 | 输出包含中英文混合 + emoji，不报 cp1252 错误（PYTHONUTF8=1 + read_uw_bot.py 已经验证此点）|

---

## Sources

- 现有命令：`/market-daily`、`/stock-entry`、`/stock-refresh`、`/chen-validate`
- 历史案例：POET 4/27 崩盘（-47%）作为持仓决策矩阵的设计依据
- yfinance API（实时数据源）
- 自身资本风险管理框架（1% rule, BE stop, trailing stop）
