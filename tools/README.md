# Tools

外部工具使用指引，用于金融研究和市场数据获取。

## 已安装工具

| 工具 | 用途 | 安装方式 |
|------|------|----------|
| [opencli](https://github.com/jackwener/opencli) | 读取 Twitter/X、LinkedIn、Discord（复用 Chrome session） | `npm install -g @jackwener/opencli` |
| [tdl](https://github.com/iyear/tdl) | 读取 Telegram 频道和群组 | 手动下载二进制 |
| yfinance | Yahoo Finance 股票数据 | `pip install yfinance` |

## opencli

通过 Chrome Browser Bridge 扩展复用浏览器 session，无需 API key。

**前提条件：**
- Chrome 已安装 Browser Bridge 扩展（Developer Mode 加载）
- 已在 Chrome 登录对应平台账号

**验证：**
```bash
opencli doctor
```

**支持平台：**
- `opencli twitter` — 读取 Twitter/X feed、搜索推文
- `opencli linkedin` — 读取 LinkedIn feed、搜索职位
- `opencli discord-app` — 读取 Discord 频道（需以 CDP 模式启动 Discord）

### Discord 启动说明

Discord 每次需以调试模式启动，才能被 opencli 连接。在 PowerShell 里运行：

```powershell
# 关闭现有 Discord
Get-Process Discord -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2

# 以 CDP 调试模式启动
Start-Process "C:\Users\lorra\AppData\Local\Discord\app-1.0.9234\Discord.exe" -ArgumentList "--remote-debugging-port=9232"
```

验证连接：
```bash
opencli discord-app status
```

环境变量已写入 `~/.claude/settings.json`（`OPENCLI_CDP_ENDPOINT=http://127.0.0.1:9232`），无需每次手动设置。

## tdl

Telegram CLI 工具，通过账号 session 读取频道和群组消息。

**登录（一次性，扫码）：**
```bash
tdl login -T qr
```

**常用命令：**
```bash
# 列出所有频道
tdl chat ls -f "Type contains 'channel'" -o json

# 导出最新消息
tdl chat export -c @频道名 -T last -i 20 --all --with-content -o ~/tdl-exports/output.json
```

**已订阅财经频道：**
- `@caijing_news` — 财联社
- `@zerohedge_official` — ZeroHedge
- `@MarketSentimentTg` — Market Sentiment
- `unusual_whales_crier` (ID: 5241900942) — unusual_whales bot

详见 [unusual-whales-bot.md](unusual-whales-bot.md)
