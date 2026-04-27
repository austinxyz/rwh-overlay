# finance-skills 使用指南

finance-skills 是一套金融研究 Claude skill 集合，通过自然语言触发，无需记忆命令。直接描述需求即可。

## 插件列表

| 插件 | 包含 Skills |
|------|-------------|
| finance-market-analysis | 市场分析、期权、策略、估值 |
| finance-social-readers | Twitter、LinkedIn、Telegram、Discord、YC |
| finance-data-providers | 多源情绪数据、霍尔木兹海峡、Funda AI |
| finance-startup-tools | 创业公司分析 |
| finance-ui-tools | 可交互图表和仪表盘 |
| finance-skill-creator | 创建自定义 skill |

---

## finance-market-analysis

### yfinance-data
**用途：** 从 Yahoo Finance 获取任意股票数据。
**触发：** "AAPL 的价格"、"TSLA 财报数据"、"查一下 NVDA 的期权链"
**能查：** 价格/历史K线、财务报表、分红、期权链、分析师评级、机构持仓、内部人交易、行业/板块数据、新闻

### earnings-preview
**用途：** 财报前简报——分析师预期、历史超/未达预期记录。
**触发：** "AAPL 下周财报预期"、"TSLA 财报前分析"、"NVDA 这次能 beat 吗"

### earnings-recap
**用途：** 财报后复盘——实际 vs 预期、超/未达幅度、股价反应。
**触发：** "MSFT 财报结果怎么样"、"GOOGL 有没有 beat"、"财报后股价为什么跌"

### estimate-analysis
**用途：** 分析师预期趋势和修正方向——EPS/营收预期随时间的变化。
**触发：** "NVDA 的 EPS 预期趋势"、"分析师最近上调还是下调了"、"预期修正分析"

### options-payoff
**用途：** 生成可交互的期权收益曲线图（Black-Scholes 定价）。
**触发：** 分享期权仓位截图、"画一下这个 straddle 的收益曲线"、"iron condor 的 P&L 图"
**支持策略：** butterfly、spread、straddle、strangle、condor、covered call、protective put 等

### etf-premium
**用途：** 计算 ETF 相对 NAV 的溢价/折价。
**触发：** "SPY 有没有溢价"、"IBIT 溢价多少"、"债券 ETF 折价分析"

### sepa-strategy
**用途：** 用 Mark Minervini 的 SEPA 方法分析成长股入场点。
**触发：** "这只股票符合 SEPA 标准吗"、"VCP 形态"、"Stage 2 判断"、"突破量能确认"
**核心：** 趋势模板（均线堆叠）、波动收缩形态、精确入场点、止损位

### stock-correlation
**用途：** 找相关股票、配对交易分析。
**触发：** "什么股票和 NVDA 相关"、"AMD 和 AVGO 的相关性"、"半导体板块同涨同跌的股票"

### stock-liquidity
**用途：** 分析股票流动性——买卖价差、成交量、市场冲击成本。
**触发：** "这只股票流动性怎么样"、"大单进出会不会影响价格"、"ADTV 分析"

### saas-valuation-compression
**用途：** 分析 SaaS 公司各轮融资之间的估值倍数压缩/扩张。
**触发：** "这家公司 A 轮到 B 轮估值倍数变化"、"ARR multiple 压缩原因"、"SaaS 估值分析"

---

## finance-social-readers

> 所有 social reader 均通过 opencli 或 tdl 工具，详见 [README.md](README.md)

### twitter-reader
**用途：** 读取 Twitter/X 的市场讨论、情绪、热点。
**触发：** "搜一下 POET 的 Twitter 讨论"、"fintwit 在说什么"、"查 @用户名 的推文"
**要求：** Chrome 登录 x.com + Browser Bridge 扩展

### linkedin-reader
**用途：** 读取 LinkedIn feed、搜索行业职位。
**触发：** "LinkedIn 上有没有人讨论 NVDA"、"搜量化分析师职位"
**要求：** Chrome 登录 linkedin.com + Browser Bridge 扩展

### telegram-reader
**用途：** 读取 Telegram 频道和群组消息。
**触发：** "读一下财联社最新内容"、"ZeroHedge 今天说了什么"
**要求：** tdl 已登录（`tdl login -T qr`）
**已订阅频道：** 财联社、ZeroHedge、Market Sentiment、unusual_whales bot

### discord-reader
**用途：** 读取 Discord 服务器频道消息。
**触发：** "读一下这个交易 Discord 的讨论"、"搜 BTC 相关消息"
**要求：** Discord 以 CDP 模式启动（见 README.md）

### yc-reader
**用途：** 读取 Y Combinator Hacker News 的讨论。
**触发：** "HN 上在讨论什么 AI 话题"、"YC 创始人对 XX 的看法"

---

## finance-data-providers

### finance-sentiment
**用途：** 跨平台情绪数据——Reddit、X.com、新闻、Polymarket。
**触发：** "TSLA 的社交情绪"、"NVDA 在 Reddit 有多热"、"对比 AMD 和 NVDA 的情绪"、"Polymarket 上有没有投注"

### funda-data
**用途：** Funda AI API——覆盖范围最广的数据源。
**触发：** 财务数据、SEC 文件、期权流/GEX、供应链图、国会交易、宏观经济数据、AI 招聘信号等
**特色：** AI 增强新闻（情绪+事件时间线）、产品发布概率、AI 对上市公司的威胁分析

### hormuz-strait
**用途：** 霍尔木兹海峡实时状态——油轮通行、战争风险溢价、外交动态。
**触发：** "霍尔木兹海峡现在安全吗"、"中东石油运输风险"、"波斯湾航运"

---

## finance-startup-tools

### startup-analysis
**用途：** 从三个视角分析创业公司：VC 投资人、求职者、CEO。
**触发：** "分析一下这家公司"、"这个 offer 值得接吗"、"这家创业公司值得投资吗"

---

## finance-ui-tools

### generative-ui
**用途：** 生成可交互的 HTML 图表和仪表盘（内嵌在对话中）。
**触发：** "画一个图"、"可视化这些数据"、"做一个比较表格"、"加滑块控制"
**支持：** K线图、相关性热力图、期权收益图、财务仪表盘、流程图等

---

## 使用示例

```
# 财报分析
"帮我做一个 POET 的财报前简报"
"NVDA 上季度财报结果如何"

# 期权分析
"画一下买入 AAPL 300 call 的收益曲线"
"POET 的 max pain 在哪里"

# 社交情绪
"搜一下 Twitter 上关于 POET 的最新讨论"
"财联社今天有什么重要快讯"

# 技术分析
"用 SEPA 方法分析一下 POET"
"POET 和哪些股票相关性高"

# 宏观/地缘
"霍尔木兹海峡今天状态怎样"
"国会议员最近在买什么"
```
