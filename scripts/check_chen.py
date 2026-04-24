#!/usr/bin/env python3
"""
check_chen.py — 检测 chen.md 是否有新内容需要导入到 chen-yun.md

用法：
    py scripts/check_chen.py

返回：
    - 如果有新内容（源文件日期 > wiki 最后导入日期），打印差异摘要
    - 如果已是最新，打印"已是最新"
"""

import re
import sys
from pathlib import Path

OVERLAY_DIR = Path(__file__).parent.parent
SOURCE = Path(r"C:\Users\lorra\projects\personal\stock\analysis\opinion\chen.md")
WIKI   = OVERLAY_DIR / "wiki" / "opinions" / "chen-yun.md"


def extract_latest_date_from_source(text: str) -> str:
    """从源文件的股票汇总表或标题中提取最新日期（格式 YYYY-MM-DD 或 M/D）。"""
    # 优先读标题中的截图日期范围
    m = re.search(r"截图时间范围.*?~\s*(\d{4}-\d{2}-\d{2}|\d+/\d+)", text)
    if m:
        raw = m.group(1)
        if "/" in raw:
            month, day = raw.split("/")
            return f"2026-{int(month):02d}-{int(day):02d}"
        return raw

    # 回退：找时间线里最新的日期标题（### M/D 或 ### YYYY-MM-DD）
    dates = re.findall(r"###\s+(\d{4}-\d{2}-\d{2}|\d+/\d+)", text)
    if not dates:
        return "unknown"
    raw = dates[0]
    if "/" in raw:
        month, day = raw.split("/")
        return f"2026-{int(month):02d}-{int(day):02d}"
    return raw


def extract_last_import_from_wiki(text: str) -> str:
    """从 wiki 文件的 frontmatter 中读取最后导入日期。"""
    m = re.search(r"\*\*最后导入\*\*:\s*(\d{4}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    return "unknown"


def extract_timeline_entries(text: str):
    """提取时间线中所有日期条目，返回 {date_str: section_text} 字典。"""
    entries = {}
    pattern = re.compile(r"###\s+(\d+/\d+)（.*?）?\n(.*?)(?=\n###|\Z)", re.DOTALL)
    for m in pattern.finditer(text):
        month, day = m.group(1).split("/")
        key = f"2026-{int(month):02d}-{int(day):02d}"
        entries[key] = m.group(2).strip()
    return entries


def main():
    if not SOURCE.exists():
        print(f"❌ 源文件不存在: {SOURCE}")
        sys.exit(1)
    if not WIKI.exists():
        print(f"❌ wiki 文件不存在: {WIKI}")
        sys.exit(1)

    source_text = SOURCE.read_text(encoding="utf-8")
    wiki_text   = WIKI.read_text(encoding="utf-8")

    source_latest = extract_latest_date_from_source(source_text)
    wiki_last     = extract_last_import_from_wiki(wiki_text)

    print(f"源文件最新日期：{source_latest}")
    print(f"Wiki 最后导入：{wiki_last}")

    if source_latest <= wiki_last:
        print("✅ 已是最新，无需更新。")
        sys.exit(0)

    print(f"\n⚠️  发现新内容（{wiki_last} → {source_latest}），请让 Claude 处理以下日期：")

    # 找出源文件中比 wiki_last 更新的时间线条目
    source_entries = extract_timeline_entries(source_text)
    new_dates = sorted(
        [d for d in source_entries if d > wiki_last],
        reverse=True
    )

    if new_dates:
        for d in new_dates:
            preview = source_entries[d][:120].replace("\n", " ")
            print(f"  • {d}：{preview}…")
    else:
        print("  （无法自动解析具体条目，请手动对比源文件）")

    print(f"\n运行提示：告诉 Claude「chen.md 有更新，请同步到 chen-yun.md」即可。")
    print(f"新日志文件将写入：{OVERLAY_DIR / 'wiki' / 'opinions' / 'chen-yun-log'}/")
    sys.exit(1)  # 非零退出码表示需要更新


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
