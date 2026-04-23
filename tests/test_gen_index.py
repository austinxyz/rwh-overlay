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


def test_handles_empty_tickers_dir(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "tickers").mkdir(parents=True)
    out = tmp_path / "index.md"
    r = run_script(wiki, out)
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")
    assert "## Upstream Tickers" in text
    assert "_(none)_" in text
