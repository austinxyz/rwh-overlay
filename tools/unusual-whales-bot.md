# unusual_whales Telegram Bot

- **Bot 显示名：** unusual_whales_crier
- **Username：** OpenBBBot
- **Chat ID：** 5241900942

导出消息：
```bash
tdl chat export -c 5241900942 -T last -i 20 --all --with-content -o ~/tdl-exports/uw_bot.json
```

## 图标说明

| 图标 | 含义 |
|------|------|
| 🇹 | 需要指定 ticker |
| 🇳 | 非指数 ticker |
| 🇨 | 需要指定合约 |
| 🇪 | 需要指定到期日 |
| 🔒 | 免费版部分内容锁定 |
| 👁️ | 免费版使用 15 分钟延迟数据 |
| 🛠️ | 高级版有额外交互功能 |

## General Information

| 命令 | 说明 |
|------|------|
| `/screener` 👁️ 🛠️ | 多种预设筛选视图 |
| `/company` 🇹 | 公司基本信息摘要 |
| `/economic_calendar` | 即将到来的经济事件日历 |
| `/fda_calendar` | 即将到来的 FDA 事件日历 |
| `/market_holiday` | 市场（早盘）休市日历 |
| `/market_tide` 👁️ 🛠️ | 每日市场潮汐 |
| `/news` 🇹 | 指定 ticker 的最新文章 |
| `/news_latest` | 最新重要文章 |
| `/overview` 🇹 | Ticker 期权概览 |
| `/price` 👁️ | Ticker 价格和成交量 |
| `/heatmaps` 👁️ | 涨跌幅和 P/C 热力图 |

## Flow（期权流）

| 命令 | 说明 |
|------|------|
| `/flow` 🔒 🛠️ | 最新期权交易 |
| `/flow_alerts` 🇳 | 最新期权流警报 |
| `/flow_expiry` 👁️ 🇹 | 按到期日的 OI 和成交量 |

## Volume（成交量）

| 命令 | 说明 |
|------|------|
| `/highest_volume_contracts` | 成交量最高的合约 |
| `/options_volume` 👁️ 🛠️ 🇹 | Ticker 每日期权活动 |
| `/contract_volume` 👁️ 🛠️ 🇨 | 合约每日活动 |
| `/historical_volume` 🇹 | 每日 Put/Call 成交量 |
| `/cumulative_volume` 🇹 | 跨到期日累计成交量 |
| `/trading_above_average` | 超过 30 日均量（按市值）|

## Open Interest（未平仓量）

| 命令 | 说明 |
|------|------|
| `/oi_change` 🇹 | OI 增减最多的合约 |
| `/oi_increase` | OI 增加最多的合约 |
| `/oi_decrease` | OI 减少最多的合约 |
| `/oi_highest` 🇹 | OI 最高的合约 |
| `/oi_expiry` 👁️ 🇹 | 按到期日的 OI |
| `/oi_strike` 👁️ 🇹 | 按行权价的 OI |
| `/spx_oi` 👁️ | SPX/SPXW 按行权价的 OI |
| `/uoa_voloi` 🇹 | Vol/OI 比率最高的合约 |

## Earnings（财报）

| 命令 | 说明 |
|------|------|
| `/earnings` 🇹 | 历史财报数据 |
| `/earnings_premarket` 🔒 | 盘前财报（按 OI/Vol/市值）|
| `/earnings_afterhours` 🔒 | 盘后财报（按 OI/Vol/市值）|

## Sector（行业）

| 命令 | 说明 |
|------|------|
| `/sectorflow` | 各行业期权活动 |
| `/sectorflowtop` | 行业内最高溢价交易 |
| `/sectorview` | 行业内按权重排名的 ticker |

## Congress（国会）

| 命令 | 说明 |
|------|------|
| `/congress_late` | 最近逾期披露的国会交易 |
| `/congress_recent` | 国会最新交易 |
| `/congress_trader` | 指定国会议员的最新交易 |
| `/congress_trades` 🇹 | Ticker 的国会交易（按议员）|

## Darkpool（暗池）

| 命令 | 说明 |
|------|------|
| `/darkpool_recent` | 最新暗池交易（按时间）|
| `/darkpool_ticker` 🇳 | 指定 ticker 的暗池交易 |

## ETF

| 命令 | 说明 |
|------|------|
| `/etf_perf` 🇹 | ETF 成分股按涨跌幅 |
| `/etf_weight` 🇹 | ETF 成分股按权重 |

## Short Interest（做空）

| 命令 | 说明 |
|------|------|
| `/short_cboe_volume` 🇹 | CBOE 做空成交量 |
| `/short_failures_to_deliver` 🇹 | 每日交割失败数据 |
| `/short_interest_volume` 🇹 | 做空成交量、价格和股数 |

## Historical（历史数据）

| 命令 | 说明 |
|------|------|
| `/historical_dividends` 🇹 | 历史分红数据 |
| `/historical_performance` 🇹 | 历史成交量和价格 |
| `/historical_options` 🛠️ 🇹 | 历史 P/C 比率、成交量、多头溢价 |
| `/historical_price` 🇹 | 历史价格（按日/年）|
| `/historical_splits` 🇹 | 历史股票拆分 |
| `/seasonality_avg_return` 🇳 | 每月平均回报率 |

## Other

| 命令 | 说明 |
|------|------|
| `/chart` 🇹 | K 线图和成交量（含可选指标）|
| `/implied` 🔒 🇹 🇪 | 隐含波动率、预期波动区间 |
| `/max_pain` 🇹 🇪 | 各行权价的最大痛苦点 |
| `/hottest_chains_bearish` | 空头溢价最高的合约 |
| `/hottest_chains_bullish` | 多头溢价最高的合约 |
| `/52_week_high` | 52 周高点 ticker（按市值/成交量/涨幅）|
| `/52_week_low` | 52 周低点 ticker（按市值/成交量/跌幅）|
