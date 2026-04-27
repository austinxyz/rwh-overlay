# 整合研究命令系统 — 需求文档

**Date:** 2026-04-26  
**Owner:** austinxyz  
**Status:** Draft — 待分阶段实现

---

## 背景

rwh-overlay 目前已有 `/market-daily` 命令和 finance-skills 工具集。本文档定义将两者整合后的完整命令体系，覆盖个股研究、Chen Yun 观点验证、市场发现、买卖点分析、以及周/月/季报。

**实现路径：** 先做成 Claude Code 命令（`.claude/commands/`），成熟后迁移为 Plugin Skill。

---

## 命令总览

| 命令 | 分类 | 优先级 |
|------|------|--------|
| `/stock-analyze <TICKER>` | 个股深度分析 | P1 |
| `/stock-entry <TICKER>` | 买入/卖出点 | P1 |
| `/chen-integrate` | Chen 观点整合 | P1 |
| `/chen-validate <TICKER>` | Chen 观点社交验证 | P1 |
| `/market-daily`（增强） | 每日日报 + 潜力股发现（合并） | P1（已有，增强）|
| `/market-weekly` | 周报 | P2 |
| `/market-monthly` | 月报 | P3 |
| `/market-quarterly` | 季报 | P3 |

---

## 功能详述

### F1. `/stock-analyze <TICKER>` — 个股深度分析

**目的：** 用 finance-skills 工具补充数据，生成符合 upstream 15 节 thesis 框架的完整个股研究。

**触发方式：** 手动，传入 ticker symbol。

**执行步骤：**
1. 用 `yfinance-data` 拉取公司基本信息、财务报表、分析师评级
2. 用 `estimate-analysis` 分析预期修正趋势（上调还是下调）
3. 用 `earnings-recap` / `earnings-preview` 补充财报历史和下次预期
4. 用 `sepa-strategy` 评估技术面（趋势模板、入场质量）
5. 用 `stock-correlation` 找相关标的（竞争对手、供应链）
6. 用 `finance-sentiment` 检查当前社交情绪（Reddit/X/新闻）
7. 用 `stock-liquidity` 评估流动性（大单进出影响）
8. 综合以上生成分析草稿，按 upstream 框架组织

**输出：**
- 交互式草稿，逐节确认
- 用户确认后写入 `wiki/tickers/<TICKER>/`（overview.md + thesis.md + financials.md）
- 同时生成中文版（`.zh.md`）

**与现有系统的关系：** 替代目前纯手动写作的方式，数据采集自动化，分析结构不变。

---

### F2. `/stock-entry <TICKER>` — 买入/卖出点分析

**目的：** 对已研究的标的，给出具体的入场价、止损位、目标价和仓位建议。

**触发方式：** 手动，on-demand。

**执行步骤：**
1. 用 `sepa-strategy` 评估当前技术面位置（Stage 分析、VCP 形态、pivot point）
2. 用 `yfinance-data` 获取实时价格、ATR（平均真实波动范围）
3. 用 `stock-liquidity` 评估执行成本（滑点估算）
4. 用 `options-payoff` 可视化潜在风险/收益（如有期权仓位意图）
5. 用 `oi_strike` / `max_pain`（unusual_whales bot）确认期权市场关键价位
6. 综合输出结构化建议

**输出格式：**
```
入场区间：$XX.XX — $XX.XX
止损位：$XX.XX（风险：X%）
目标价 1：$XX.XX（盈亏比 X:1）
目标价 2：$XX.XX（盈亏比 X:1）
建议仓位：占总仓位 X%（基于 1% 本金风险）
当前技术位：Stage X，[形态描述]
期权 Max Pain（最近到期）：$XX
```

**输出文件：** `wiki/tickers/<TICKER>/entry-YYYY-MM-DD.md`（带日期，可追踪历次分析）

**联动更新：**
- `wiki/tickers/<TICKER>/changelog.md` — 追加一条记录（日期 + 入场价/止损/目标价摘要）
- `wiki/tickers/<TICKER>/overview.md` — 在"历史入场分析"节添加链接，指向 `entry-YYYY-MM-DD.md`（节不存在则新增）

---

### F3. `/chen-integrate` — Chen Yun 观点整合

**目的：** 将 `raw/analyses/chen.md` 的最新内容解析并写入日志，同时标记需要社交验证的 ticker。

**触发方式：** 手动，每次 Chen 有新内容时运行。

**执行步骤：**
1. 读取 `raw/analyses/chen.md`，识别新增内容（对比最近一条日志）
2. 提取：每个 ticker、推荐强度（🔥数量）、Chen 原话、观点类型（首推/加仓/止损等）
3. 写入 `wiki/opinions/chen-yun-log/YYYY-MM-DD.md`，内容包含两部分：
   - 当日观点摘录（主体）
   - 验证清单（文件末尾）

**日志文件结构：**
```markdown
# Chen-Yun 日志 — YYYY-MM-DD

- **TICKER** — [观点摘要，🔥强度]

---

## 建议社交验证

| Ticker | 原因 | 状态 |
|--------|------|------|
| ATOM | 首次推荐，🔥🔥🔥 | 待验证 |
| WOLF | 连续 3 日提及 | 待验证 |
```

4. 向用户展示验证清单，等待决定是否执行 `/chen-validate`

**验证触发条件：**
- 首次出现的新 ticker
- 🔥🔥🔥 级别的强推
- 近期连续多日提及（≥3 日）

**与现有系统的关系：** 替代目前的 `scripts/check_chen.py`，整合验证步骤。

---

### F4. `/chen-validate <TICKER>` — Chen 观点社交验证

**目的：** 对 Chen 力推的 ticker，用社交和市场数据交叉验证，判断观点是否有共鸣。

**触发方式：** 手动，通常由 `/chen-integrate` 建议后执行。

**执行步骤：**
1. 用 `twitter-reader` 搜索近期推文（情绪、讨论量）
2. 用 `finance-sentiment` 获取 Reddit/X/新闻跨平台情绪分数
3. 用 `yfinance-data` 查近期价格走势和成交量异动
4. 查 unusual_whales bot：`/darkpool_ticker`、`/flow_alerts`（期权异动）
5. 用 `estimate-analysis` 看分析师预期方向是否配合

**输出：**

验证结果追加写入当日 chen-yun-log 文件，更新对应 ticker 的验证状态：

```markdown
## 建议社交验证

| Ticker | 原因 | 状态 | 综合评估 |
|--------|------|------|----------|
| ATOM | 首次推荐，🔥🔥🔥 | ✅ 已验证 | 配合（情绪偏多，期权异动） |
| WOLF | 连续 3 日提及 | 待验证 | — |

### ATOM 验证详情
- Twitter 情绪：偏多，讨论量高
- Reddit 情绪：[分数]
- 期权流：异常（大宗看涨）
- 近期量价：突破
- 分析师预期：上调

**综合评估：** 配合
**建议：** 可进一步研究 → 运行 `/stock-analyze ATOM`？
```

6. 向用户询问是否继续执行 `/stock-analyze <TICKER>`

---

### F5. `/market-daily`（增强版）— 每日综合日报

**目的：** 合并每日市场日报 + 潜力股发现，生成一份综合日报，保存在 `wiki/market/` 下。

**输出文件：** `wiki/market/YYYY-MM-DD.md`（与现有格式兼容，新增章节）

**报告结构（完整版）：**

```markdown
# 市场日报 · YYYY-MM-DD

## 市场情绪
Fear & Greed: XX (Label) ↑ 昨日 XX
社交情绪（Reddit/X）：[偏多/中性/偏空]

## 主要指数
| 指数 | 收盘 | 涨跌幅 |
...

## 板块表现
领涨/领跌...

## Watchlist 个股
...

## 市场异常信号
- 期权流：[unusual_whales flow_alerts 当日信号]
- 暗池：[darkpool_recent 大单]
（无显著信号则略去本节）

## 今日要闻
...

## AI 解读
**市场概况：** ...
**板块轮动：** ...
**Watchlist 亮点：** ...
**市场异常信号：** ...

## 今日潜力股候选
（四维筛选：技术 + 情绪 + 期权流 + 基本面，至少 3/4 维正向）

| Ticker | 技术 | 情绪 | 期权流 | 基本面 | 总分 |
|--------|------|------|--------|--------|------|
| XXXX   | ✅   | ✅   | ✅     | ⚠️     | 3/4  |

**简评：**
- XXXX：[1-2 句说明信号来源]
```

**潜力股筛选逻辑（四维综合）：**

| 维度 | 工具 | 判断标准 |
|------|------|----------|
| 技术面 | `sepa-strategy` | Stage 2、趋势模板达标、量能配合 |
| 社交情绪 | `finance-sentiment` + `twitter-reader` | 情绪上升且讨论量增加 |
| 期权流 | unusual_whales `/trading_above_average` + `/flow_alerts` | 异常成交量或大宗看涨 |
| 基本面 | `estimate-analysis` | 近期分析师预期上调 |

**执行顺序（扩展现有步骤）：**
1. 现有步骤：Python 脚本抓数据 → 写市场/指数/板块/watchlist/新闻
2. 新增：`finance-sentiment` 获取社交情绪
3. 新增：unusual_whales bot 获取异常信号（`/flow_alerts`、`/darkpool_recent`）
4. 新增：潜力股筛选（`/trading_above_average`、`/52_week_high`、`/hottest_chains_bullish` → `sepa-strategy` + `estimate-analysis` 过滤）
5. 综合写入单一日报文件

**周末版：** 不含板块/指数/watchlist/潜力股，仅保留情绪 + 要闻 + AI 解读。

---

### F6. `/market-weekly` — 周报

**目的：** 每周五或周末运行，回顾本周 + 展望下周。

**回顾部分：**
- 主要指数周涨跌
- 行业表现排名（本周领涨/领跌）
- Watchlist 个股周表现，对比 thesis 的吻合度
- 重大事件复盘（财报、宏观数据、地缘）
- 本周日报中潜力股候选的后续表现追踪

**展望部分：**
- 用 unusual_whales bot `/economic_calendar` 获取下周重要事件
- 用 `/earnings_premarket` + `/earnings_afterhours` 提示下周财报
- AI 解读：下周关键风险和机会，watchlist 需要关注的节点

**输出：** `wiki/market/weekly-YYYY-WXX.md`

---

### F7. `/market-monthly` — 月报

**目的：** 每月最后一个交易日运行，月度回顾 + 下月展望。

**回顾部分：**
- 月度市场表现 vs 标普500
- Watchlist 个股月度盈亏，thesis 验证进度
- 本月 Chen 观点的命中率复盘（对比 chen-yun-log 和实际走势）
- 本月日报潜力股候选的胜率统计

**展望部分：**
- 宏观环境评估（利率、就业、通胀方向）
- 行业轮动信号（下月偏向哪个板块）
- Watchlist 调整建议：是否有 ticker 应加入或移除

**输出：** `wiki/market/monthly-YYYY-MM.md`

---

### F8. `/market-quarterly` — 季报

**目的：** 每季度末运行，季度总结 + 下季展望。

**回顾部分：**
- 季度市场表现 vs 基准
- Watchlist 季度盈亏，各 thesis 的成立与否
- 财报季整体分析（哪些行业超预期/不及预期）
- `saas-valuation-compression` 用于科技/SaaS 标的估值变化分析

**展望部分：**
- 下季宏观主题（Fed 路径、全球风险）
- 下季财报季预期（用 `estimate-analysis` 对重点 ticker）
- Watchlist 重新审视：是否需要更新 thesis

**输出：** `wiki/market/quarterly-YYYY-QX.md`

---

## 实现阶段建议

### Phase 1（核心研究工具）
- `/stock-analyze` — 个股分析自动化
- `/stock-entry` — 买卖点（输出至 `wiki/tickers/<TICKER>/entry-YYYY-MM-DD.md`）
- `/chen-integrate` + `/chen-validate` — Chen 观点整合 + 验证（结果写回日志）

### Phase 2（市场发现，增强日报）
- `/market-daily` 增强：加社交情绪、期权流异常信号、潜力股候选节（合并原 `/market-discover`）

### Phase 3（周期报告）
- `/market-weekly`
- `/market-monthly`
- `/market-quarterly`

---

## 文件输出一览

| 命令 | 输出路径 |
|------|----------|
| `/stock-analyze` | `wiki/tickers/<TICKER>/{overview,thesis,financials}.md` + `.zh.md` |
| `/stock-entry` | `wiki/tickers/<TICKER>/entry-YYYY-MM-DD.md` |
| `/chen-integrate` | `wiki/opinions/chen-yun-log/YYYY-MM-DD.md` |
| `/chen-validate` | 追加更新至当日 chen-yun-log |
| `/market-daily` | `wiki/market/YYYY-MM-DD.md` + `wiki/market/index.md` |
| `/market-weekly` | `wiki/market/weekly-YYYY-WXX.md` |
| `/market-monthly` | `wiki/market/monthly-YYYY-MM.md` |
| `/market-quarterly` | `wiki/market/quarterly-YYYY-QX.md` |

---

## 依赖关系

| 命令 | 依赖的 finance-skills |
|------|----------------------|
| `/stock-analyze` | yfinance-data, estimate-analysis, earnings-recap, sepa-strategy, stock-correlation, finance-sentiment, stock-liquidity |
| `/stock-entry` | sepa-strategy, yfinance-data, stock-liquidity, options-payoff, unusual_whales bot |
| `/chen-validate` | twitter-reader, finance-sentiment, yfinance-data, unusual_whales bot, estimate-analysis |
| `/market-daily`（增强） | finance-sentiment, twitter-reader, sepa-strategy, estimate-analysis, unusual_whales bot |
| `/market-weekly` | yfinance-data, unusual_whales bot（economic_calendar, earnings） |
| `/market-monthly` | yfinance-data, finance-sentiment |
| `/market-quarterly` | yfinance-data, estimate-analysis, saas-valuation-compression |
