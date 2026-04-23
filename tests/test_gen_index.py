import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "gen_index.py"
FIXTURE = Path(__file__).parent / "fixtures" / "sample_tickers"


def run_script(wiki_root, output):
    return subprocess.run(
        [sys.executable, str(SCRIPT),
         "--wiki-root", str(wiki_root),
         "--output", str(output)],
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


def test_handles_empty_tickers_dir(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "tickers").mkdir(parents=True)
    out = tmp_path / "index.md"
    r = run_script(wiki, out)
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")
    assert "## Upstream Tickers" in text
    assert "_(none)_" in text
