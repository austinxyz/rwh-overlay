import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "gen_index.py"
FIXTURE = Path(__file__).parent / "fixtures" / "sample_tickers"


def run_script(wiki_root, output, lang="en"):
    return subprocess.run(
        [sys.executable, str(SCRIPT),
         "--wiki-root", str(wiki_root),
         "--output", str(output),
         "--lang", lang],
        capture_output=True, text=True, check=False,
    )


def test_generates_two_tables_grouped_by_source(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "tickers").mkdir(parents=True)
    import shutil
    for d in FIXTURE.iterdir():
        shutil.copytree(d, wiki / "tickers" / d.name)

    out = tmp_path / "index.md"
    r = run_script(wiki, out)
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")

    assert "## Upstream Tickers" in text
    assert "## My Tickers" in text
    ups_a = text.index("UPS_A")
    ups_c = text.index("UPS_C")
    assert ups_a < ups_c
    aus_b = text.index("AUS_B")
    my_heading = text.index("## My Tickers")
    assert aus_b > my_heading
    assert "Fake upstream ticker A for index tests." in text
    assert "2026-04-22" in text


def test_extracts_summary_and_updated_from_body_when_missing_in_frontmatter(tmp_path):
    """Most overview.md files don't have summary/updated in frontmatter;
    the generator must fall back to parsing the body. Two body formats exist:
      - upstream: `> **Last Updated**: 2026-04-05` (blockquote)
      - overlay:  `**Last updated**: 2026-04-22` (bare)
    """
    wiki = tmp_path / "wiki"
    (wiki / "tickers" / "UPS_BQ").mkdir(parents=True)
    (wiki / "tickers" / "UPS_BQ" / "overview.md").write_text(
        "---\nsource: upstream\n---\n"
        "# UPS_BQ — Overview\n\n"
        "> **Status**: Active — compiled 2026-04-05\n"
        "> **Last Updated**: 2026-04-05\n"
        "> **Moat**: Wide\n\n"
        "---\n\n"
        "## Business Description\n\n"
        "This is the first prose paragraph of UPS_BQ, long enough to qualify"
        " as a summary for the index table.\n",
        encoding="utf-8",
    )
    (wiki / "tickers" / "AUS_BARE").mkdir(parents=True)
    (wiki / "tickers" / "AUS_BARE" / "overview.md").write_text(
        "---\nsource: austin\n---\n"
        "# AUS_BARE — Overview\n\n"
        "**Last updated**: 2026-04-22\n"
        "**Status**: Active — initial thesis\n\n"
        "---\n\n"
        "## Business in One Line\n\n"
        "Pure-play designer of wide-bandgap power semiconductors with a"
        " pivot into the high-power AI datacenter market.\n",
        encoding="utf-8",
    )
    out = tmp_path / "index.md"
    r = run_script(wiki, out)
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")

    # Dates pulled from body
    assert "2026-04-05" in text
    assert "2026-04-22" in text
    # Summary first prose paragraph
    assert "first prose paragraph of UPS_BQ" in text
    assert "wide-bandgap power semiconductors" in text
    # Bold markers stripped from summaries
    assert "**Status**" not in text


def test_updated_falls_back_to_changelog_latest_date(tmp_path):
    """When overview.md has no 'Last Updated' line, pull the date from the
    most recent changelog heading (supports bracketed and bare variants)."""
    wiki = tmp_path / "wiki"
    (wiki / "tickers" / "NOUP").mkdir(parents=True)
    (wiki / "tickers" / "NOUP" / "overview.md").write_text(
        "---\nsource: upstream\n---\n# NOUP — Some Ticker\n\n"
        "## Business Description\n\n"
        "A business description long enough to be treated as a summary for"
        " the index table.\n",
        encoding="utf-8",
    )
    (wiki / "tickers" / "NOUP" / "changelog.md").write_text(
        "# NOUP — Changelog\n\n"
        "## [2026-04-06] — Latest\n\nNewer entry.\n\n"
        "## [2026-03-01] — Older\n\nOlder entry.\n",
        encoding="utf-8",
    )
    out = tmp_path / "index.md"
    r = run_script(wiki, out)
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")
    noup_row = [l for l in text.splitlines() if "NOUP" in l and "|" in l][0]
    assert "2026-04-06" in noup_row
    assert "2026-03-01" not in noup_row


def test_summary_truncates_long_paragraphs(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "tickers" / "LONG").mkdir(parents=True)
    body = "word " * 200  # ~1000 chars
    (wiki / "tickers" / "LONG" / "overview.md").write_text(
        "---\nsource: austin\n---\n# LONG\n\n" + body + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "index.md"
    r = run_script(wiki, out)
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")
    # Find the LONG row
    long_row = [l for l in text.splitlines() if "LONG" in l and "|" in l][0]
    # Truncation marker present
    assert "…" in long_row


def test_zh_mode_prefers_overview_zh_when_present(tmp_path):
    """zh mode should read overview.zh.md for the Chinese summary and link to it,
    while falling back to overview.md for tickers without a Chinese variant."""
    wiki = tmp_path / "wiki"
    # Ticker with BOTH English and Chinese overviews
    (wiki / "tickers" / "BILING").mkdir(parents=True)
    (wiki / "tickers" / "BILING" / "overview.md").write_text(
        "---\nsource: austin\nticker: BILING\n---\n"
        "# BILING — Overview\n\n"
        "**Last updated**: 2026-04-22\n\n"
        "---\n\n"
        "## Business\n\n"
        "English business description long enough to be used as a summary.\n",
        encoding="utf-8",
    )
    (wiki / "tickers" / "BILING" / "overview.zh.md").write_text(
        "# BILING — 概况\n\n"
        "**最后更新**: 2026-04-22\n\n"
        "---\n\n"
        "## 业务简介\n\n"
        "这是一段足够长的中文业务描述，用作索引表里的摘要栏。确保不会被丢弃。\n",
        encoding="utf-8",
    )
    # Ticker with only English (upstream-style) — zh mode should fall back
    (wiki / "tickers" / "ENONLY").mkdir(parents=True)
    (wiki / "tickers" / "ENONLY" / "overview.md").write_text(
        "---\nsource: upstream\nticker: ENONLY\n---\n"
        "# ENONLY — Overview\n\n"
        "> **Last Updated**: 2026-04-05\n\n"
        "---\n\n"
        "## Business\n\n"
        "English-only fallback prose paragraph for a ticker with no zh.md.\n",
        encoding="utf-8",
    )

    out = tmp_path / "index.zh.md"
    r = run_script(wiki, out, lang="zh")
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")

    # Localized headings and labels
    assert "# 股票索引" in text
    assert "## 上游股票" in text
    assert "## 我的股票" in text
    assert "| Ticker | 摘要 | 更新于 |" in text

    # BILING row uses Chinese summary and links to .zh.md
    assert "这是一段足够长的中文业务描述" in text
    assert "tickers/BILING/overview.zh.md" in text
    # BILING gets its Chinese **最后更新** field recognized
    assert "2026-04-22" in text

    # ENONLY row falls back to English content, links to overview.md
    assert "English-only fallback prose" in text
    assert "tickers/ENONLY/overview.md" in text
    assert "2026-04-05" in text


def test_zh_mode_inherits_source_from_english_overview(tmp_path):
    """overview.zh.md files don't get source: frontmatter injected by the
    build (inject_frontmatter runs once on each file). zh mode must look at
    the sibling overview.md to classify upstream vs austin."""
    wiki = tmp_path / "wiki"
    (wiki / "tickers" / "ZHONLY").mkdir(parents=True)
    (wiki / "tickers" / "ZHONLY" / "overview.md").write_text(
        "---\nsource: austin\nticker: ZHONLY\n---\n# ZHONLY\n\n"
        "## Business\n\nEnglish prose that wouldn't be used in zh mode.\n",
        encoding="utf-8",
    )
    (wiki / "tickers" / "ZHONLY" / "overview.zh.md").write_text(
        # No frontmatter at all on zh file
        "# ZHONLY — 概况\n\n## 业务\n\n"
        "这是一段足够长的中文业务描述，不含 frontmatter，须正确归到「我的股票」下。\n",
        encoding="utf-8",
    )
    out = tmp_path / "index.zh.md"
    r = run_script(wiki, out, lang="zh")
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")
    # ZHONLY should appear under My Tickers (austin), not Upstream
    my_start = text.index("## 我的股票")
    zhonly_pos = text.index("ZHONLY")
    assert zhonly_pos > my_start


def test_handles_empty_tickers_dir(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "tickers").mkdir(parents=True)
    out = tmp_path / "index.md"
    r = run_script(wiki, out)
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")
    assert "## Upstream Tickers" in text
    assert "_(none)_" in text
