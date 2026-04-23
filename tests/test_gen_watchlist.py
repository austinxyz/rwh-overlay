import subprocess
import sys
from pathlib import Path
import shutil

SCRIPT = Path(__file__).parent.parent / "scripts" / "gen_watchlist.py"
FIXTURE = Path(__file__).parent / "fixtures" / "sample_tickers"


def run_script(wiki_root, output):
    return subprocess.run(
        [sys.executable, str(SCRIPT),
         "--wiki-root", str(wiki_root),
         "--output", str(output)],
        capture_output=True, text=True, check=False,
    )


def test_renders_ticker_rows_with_action_and_next_review(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "tickers").mkdir(parents=True)
    for d in FIXTURE.iterdir():
        shutil.copytree(d, wiki / "tickers" / d.name)

    out = tmp_path / "watchlist.md"
    r = run_script(wiki, out)
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")

    assert "UPS_A" in text
    assert "AUS_B" in text
    assert "Buy more" in text
    assert "Watch" in text
    assert "Strengthened" in text
    assert "Q2 2026 earnings" in text or "May 5, 2026" in text


def test_parses_changelog_without_brackets_around_date(tmp_path):
    """Some upstream tickers (BKNG, LLY, SCHW, UNH, WING) use `## 2026-04-05 — Title`
    instead of `## [2026-04-05] — Title`. Both formats must parse."""
    wiki = tmp_path / "wiki"
    (wiki / "tickers" / "NOBR").mkdir(parents=True)
    (wiki / "tickers" / "NOBR" / "overview.md").write_text(
        "---\nsource: upstream\nticker: NOBR\n---\n# No brackets\n",
        encoding="utf-8",
    )
    (wiki / "tickers" / "NOBR" / "changelog.md").write_text(
        "## 2026-04-05 — Initial Thesis Compilation\n\n"
        "### Thesis Status\n- **Overall**: Strengthened\n\n"
        "### Action\n- [x] Hold — baseline\n\n"
        "**Next review trigger**: Q1 2026 earnings\n",
        encoding="utf-8",
    )
    out = tmp_path / "watchlist.md"
    r = run_script(wiki, out)
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")
    assert "NOBR" in text
    assert "Strengthened" in text
    assert "2026-04-05" in text


def test_handles_ticker_without_changelog(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "tickers" / "NOCHG").mkdir(parents=True)
    (wiki / "tickers" / "NOCHG" / "overview.md").write_text(
        "---\nsource: austin\nticker: NOCHG\n---\n# No changelog\n",
        encoding="utf-8",
    )
    out = tmp_path / "watchlist.md"
    r = run_script(wiki, out)
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")
    assert "NOCHG" in text
    assert "_(no changelog)_" in text
