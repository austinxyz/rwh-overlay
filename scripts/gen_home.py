#!/usr/bin/env python3
"""Generate stock-kb/index.md and stock-kb/index.zh.md (Quartz home pages).

Scans wiki/tickers to count upstream vs overlay tickers and renders
a landing page with navigation links and coverage stats.

Usage:
    gen_home.py --wiki-root PATH --output PATH [--lang en|zh]
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import frontmatter

SOURCE_RE = re.compile(r"^source:\s*(\S+)", re.MULTILINE)


def count_tickers(wiki_root: Path) -> tuple[int, int]:
    """Return (upstream_count, overlay_count)."""
    tickers_dir = wiki_root / "tickers"
    if not tickers_dir.is_dir():
        return 0, 0
    upstream = overlay = 0
    for ticker_dir in tickers_dir.iterdir():
        if not ticker_dir.is_dir():
            continue
        # Prefer overview.md, fall back to TICKER.md
        candidate = ticker_dir / "overview.md"
        if not candidate.is_file():
            candidate = ticker_dir / f"{ticker_dir.name}.md"
        if not candidate.is_file():
            continue
        try:
            post = frontmatter.loads(candidate.read_text(encoding="utf-8"))
            src = post.get("source", "")
        except Exception:
            m = SOURCE_RE.search(candidate.read_text(encoding="utf-8", errors="replace"))
            src = m.group(1) if m else ""
        if src == "upstream":
            upstream += 1
        elif src == "austin":
            overlay += 1
    return upstream, overlay


HOME_EN = """\
# Stock Knowledge Base

*Austin's personal investment research wiki — upstream coverage by [kgajjala/rwh](https://github.com/kgajjala/rwh) + independent overlay research.*

*[中文版本](index.zh.md)*

---

## Navigation

| Section | Description |
|---------|-------------|
| [Ticker Index](wiki/index.md) | All covered tickers — status, moat, conviction, BAIT |
| [Watchlist](wiki/watchlist.md) | Cross-ticker attractiveness ranking |
| [Market Daily](wiki/market/index.md) | Daily market reports — indices, sectors, watchlist movers |
| [Log](wiki/log.md) | Append-only event log |
| [Chen-Yun Opinions](wiki/opinions/chen-yun.md) | Third-party opinion signals (WeChat group) |

---

## Coverage

**{total} tickers total** — {upstream} upstream (kgajjala) · {overlay} overlay (Austin)

*Last build: {today}*
"""

HOME_ZH = """\
# 股票知识库

*Austin 的个人投资研究 wiki —— 上游数据来自 [kgajjala/rwh](https://github.com/kgajjala/rwh)，另附独立 overlay 研究。*

*[English](index.md)*

---

## 导航

| 页面 | 说明 |
|------|------|
| [股票索引](wiki/index.md) | 全部覆盖标的——状态、护城河、确信度、BAIT |
| [观察列表](wiki/watchlist.zh.md) | 跨标的吸引力排名 |
| [市场日报](wiki/market/index.md) | 每日行情报告——指数、板块、Watchlist 异动 |
| [事件日志](wiki/log.md) | 追加式事件记录 |
| [陈云意见信号](wiki/opinions/chen-yun.md) | 第三方意见来源（微信群） |

---

## 覆盖范围

**共 {total} 只标的** —— 上游 {upstream} 只（kgajjala）· Overlay {overlay} 只（Austin）

*最后构建：{today}*
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wiki-root", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--lang", choices=["en", "zh"], default="en")
    args = ap.parse_args()

    upstream, overlay = count_tickers(args.wiki_root)
    total = upstream + overlay
    today = date.today().isoformat()

    template = HOME_ZH if args.lang == "zh" else HOME_EN
    content = template.format(total=total, upstream=upstream, overlay=overlay, today=today)
    args.output.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
