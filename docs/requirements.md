# rwh-overlay 功能需求文档

**Owner:** austinxyz  
**Updated:** 2026-04-27  
**Status:** Living document

---

## 概述

rwh-overlay 是一个个人股票研究知识库，整合了三个来源的内容，并提供一套辅助研究的工具：

1. **Upstream**（kgajjala/rwh）— 只读镜像，提供分析框架和标准模板
2. **个人分析**（Austin）— 基于 upstream 框架撰写的自选股研究
3. **第三方观点**（Chen Yun）— 来自 WeChat 群的市场观察，结构化整理

---

## 功能一：Stock KB 构建

**描述：** 将 upstream 和个人 overlay 合并为一个统一的股票知识库，发布到 Quartz 站点。

**入口：**
```bash
py scripts/build_stock_kb.py
```

**行为：**
- 从 `../rwh/wiki/` 读取 upstream 内容（只读，不修改）
- 合并 `wiki/tickers/`（个人覆盖）和 `wiki/opinions/`（第三方观点）
- 输出到 `../stock-kb/`（**纯文件夹，无 git**，每次构建完整重生成）
- 每个页面标注来源标签：`[Upstream]` / `[Austin]` / `[Chen via Austin]`
- 合并 `log.md`（upstream log + `overlay-log.md`）
- 单一数据源失败不阻断整体构建

**Claude 命令：**
```
/kb-sync              # 构建并同步 stock-kb（可选 --skip-pull）
```

**规则：**
- 永远不向 `../rwh/` 写入
- `../stock-kb/` 不需要 git 管理，内容从 rwh + rwh-overlay 完整重建
- `overlay-log.md` 使用裸行追加（不加 code fence）
- 个人 ticker 文件放在 `wiki/tickers/<TICKER>/`

---

## 功能二：个人股票分析

**描述：** 使用 upstream 的分析框架（15 节 thesis 标准）对自选股进行深度研究。

**文件结构：**
```
wiki/tickers/<TICKER>/
  overview.md        # 公司概览
  thesis.md          # 投资论点（15 节标准）
  financials.md      # 财务数据
  changelog.md       # 变化跟踪
  *.zh.md            # 中文翻译版（结构对应英文版）
```

**当前覆盖股票：** NVTS、OKLO、POET、WOLF、MP、INTT、EBAY

**Claude 命令：**
```
/stock-analyze <TICKER>   # 深度分析，生成完整 15 节 thesis 文件
/stock-refresh <TICKER>   # 快速刷新——有新信息时更新关键数据，不重建全文
/stock-entry <TICKER>     # 生成入场/出场点分析（entry zone、止损、目标价、期权水位）
```

**分析辅助工具（finance-skills）：**
- `/earnings-preview` — 财报前预期分析
- `/earnings-recap` — 财报后复盘
- `/estimate-analysis` — 分析师预期修正趋势
- `/sepa-strategy` — SEPA 技术面入场分析
- `/stock-correlation` — 相关股票和配对分析
- `/stock-liquidity` — 流动性和交易成本评估
- `/yfinance-data` — 任意财务数据查询

**规则：**
- 新 ticker 需通过独立 10-K/10-Q/IR 验证，不能仅凭 Chen 的观点直接建立
- 翻译版和英文版保持结构一致

---

## 功能三：Chen Yun 观点整合

**描述：** 将来自 Chen Yun WeChat 群的市场观察和选股观点结构化整理，作为研究灵感输入。

**原始输入：** `raw/analyses/chen.md`（手动更新）

**输出：**
```
wiki/opinions/chen-yun-log/YYYY-MM-DD.md   # 每日观点摘录
```

**Claude 命令：**
```
/chen-integrate   # 解析 raw/analyses/chen.md，写入每日 log，标记待验证 ticker
/chen-validate <TICKER>   # 用社交情绪/期权流/技术面交叉验证 Chen 提及的 ticker
```

**规则：**
- 仅作为 idea generation 和情绪参考，不是独立研究
- Chen 提及的 ticker 不自动升级为个人研究——需要 Austin 独立验证（`/chen-validate`）
- 不做自动化 OCR/爬虫，手动整理

---

## 功能四：每日市场日报

**描述：** 每个交易日生成一份 AI 分析的市场简报，存储为 Markdown 文件。

**Claude 命令：**
```
/market-daily      # 当日日报
/market-weekly     # 本周周报
/market-monthly    # 本月月报
/market-quarterly  # 本季季报
```

**输出：** `wiki/market/YYYY-MM-DD.md`（日报） / `wiki/market/weekly/` 等  
**索引：** `wiki/market/index.md`（自动更新）

**报告内容：**
- 主要指数：SPY、QQQ、DJI（价格、涨跌幅、成交量）
- 10 大 SPDR 行业 ETF 表现
- 自选股（自动从 `wiki/tickers/` 发现）每日价格/量
- 市场情绪：CNN Fear & Greed Index
- 重要新闻标题（Finviz）
- Claude AI 解读：关键驱动因素、行业轮动、自选股亮点
- 情绪和风险提示

**架构：**
- Layer 1（Python）：数据采集 → `scripts/gen_daily_market.py`
- Layer 2（Claude Skill）：AI 分析 + 写入 Markdown

**容错：** 任意数据源失败不阻断报告生成，降级显示可用数据

**非工作日处理：** 检测周末/节假日，自动读取最近交易日存档

---

## 功能五：Finance Skills 工具集

**描述：** 一套通过自然语言触发的金融研究工具，涵盖数据查询、社交情绪、期权分析等。

详见 [tools/finance-skills.md](../tools/finance-skills.md)

### 市场分析类
| Skill | 功能 |
|-------|------|
| `yfinance-data` | Yahoo Finance 全量数据（价格、财报、期权、持仓） |
| `earnings-preview` | 财报前预期简报 |
| `earnings-recap` | 财报后复盘 |
| `estimate-analysis` | 分析师预期修正趋势 |
| `options-payoff` | 期权收益曲线可视化 |
| `etf-premium` | ETF 溢价/折价分析 |
| `sepa-strategy` | Mark Minervini SEPA 技术分析 |
| `stock-correlation` | 相关股票和配对交易分析 |
| `stock-liquidity` | 流动性和市场冲击成本分析 |
| `saas-valuation-compression` | SaaS 融资估值倍数变化分析 |

### 社交情报类
| Skill | 数据来源 | 前提条件 |
|-------|----------|----------|
| `twitter-reader` | Twitter/X | Chrome 登录 + Browser Bridge 扩展 |
| `linkedin-reader` | LinkedIn | Chrome 登录 + Browser Bridge 扩展 |
| `telegram-reader` | Telegram 频道 | tdl 已登录 |
| `discord-reader` | Discord 服务器 | Discord 以 CDP 模式启动 |
| `yc-reader` | Hacker News | Chrome 登录 |

### 数据提供商
| Skill | 功能 |
|-------|------|
| `finance-sentiment` | Reddit/X/新闻/Polymarket 跨平台情绪 |
| `funda-data` | Funda AI API（SEC 文件、期权流、供应链、宏观） |
| `hormuz-strait` | 霍尔木兹海峡实时状态和地缘风险 |

### 其他
| Skill | 功能 |
|-------|------|
| `startup-analysis` | 创业公司三视角分析（VC/求职/CEO） |
| `generative-ui` | 可交互图表和仪表盘生成 |

---

## 相关文档

- [架构设计](superpowers/specs/2026-04-23-rwh-overlay-architecture-design.md)
- [每日市场报告设计](superpowers/specs/2026-04-25-daily-market-report-design.md)
- [工具指引](../tools/README.md)
- [Finance Skills 详细说明](../tools/finance-skills.md)
- [unusual_whales Bot 指令](../tools/unusual-whales-bot.md)
