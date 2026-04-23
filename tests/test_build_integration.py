import os
import shutil
import subprocess
import sys
from pathlib import Path

import frontmatter

REPO = Path(__file__).parent.parent
SCRIPT = REPO / "scripts" / "build_stock_kb.py"
FIXT_UP = REPO / "tests" / "fixtures" / "mock_upstream"
FIXT_OV = REPO / "tests" / "fixtures" / "mock_overlay"


def test_build_merges_and_tags(tmp_path):
    up = tmp_path / "upstream"
    ov = tmp_path / "overlay"
    out = tmp_path / "stock-kb"
    shutil.copytree(FIXT_UP, up)
    shutil.copytree(FIXT_OV, ov)
    shutil.copytree(REPO / "scripts", ov / "scripts")

    env = os.environ.copy()
    env.update({
        "RWH_DIR": str(up),
        "OVERLAY_DIR": str(ov),
        "OUTPUT_DIR": str(out),
        "SKIP_PULL": "1",
    })
    r = subprocess.run(
        [sys.executable, str(ov / "scripts" / "build_stock_kb.py")],
        capture_output=True, text=True, env=env, check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout

    # Tickers from both sides exist
    assert (out / "wiki" / "tickers" / "UPA" / "overview.md").is_file()
    assert (out / "wiki" / "tickers" / "AUB" / "overview.md").is_file()

    # Source frontmatter injected correctly
    upa = frontmatter.loads((out / "wiki" / "tickers" / "UPA" / "overview.md").read_text(encoding="utf-8"))
    aub = frontmatter.loads((out / "wiki" / "tickers" / "AUB" / "overview.md").read_text(encoding="utf-8"))
    opin = frontmatter.loads((out / "wiki" / "opinions" / "fake-source.md").read_text(encoding="utf-8"))
    assert upa.get("source") == "upstream"
    assert aub.get("source") == "austin"
    assert opin.get("source") == "austin-observation"

    # Derived files generated
    index_text = (out / "wiki" / "index.md").read_text(encoding="utf-8")
    assert "UPA" in index_text and "AUB" in index_text

    watchlist_text = (out / "wiki" / "watchlist.md").read_text(encoding="utf-8")
    assert "UPA" in watchlist_text and "AUB" in watchlist_text

    log_text = (out / "wiki" / "log.md").read_text(encoding="utf-8")
    assert "UPA" in log_text and "AUB" in log_text
    # Sorted by timestamp (04-10 before 04-22)
    assert log_text.index("UPA") < log_text.index("AUB")

    # CLAUDE files both present
    assert (out / "CLAUDE.upstream.md").is_file()
    assert (out / "CLAUDE.overlay.md").is_file()


def test_overlay_cannot_shadow_upstream_file(tmp_path):
    up = tmp_path / "upstream"
    ov = tmp_path / "overlay"
    out = tmp_path / "stock-kb"
    shutil.copytree(FIXT_UP, up)
    shutil.copytree(FIXT_OV, ov)
    shutil.copytree(REPO / "scripts", ov / "scripts")

    # Overlay tries to shadow UPA with different content
    (ov / "wiki" / "tickers" / "UPA").mkdir(parents=True)
    (ov / "wiki" / "tickers" / "UPA" / "overview.md").write_text(
        "---\nticker: UPA\nsummary: Overlay shadow attempt.\n---\n# Shadow\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env.update({"RWH_DIR": str(up), "OVERLAY_DIR": str(ov),
                "OUTPUT_DIR": str(out), "SKIP_PULL": "1"})
    r = subprocess.run(
        [sys.executable, str(ov / "scripts" / "build_stock_kb.py")],
        capture_output=True, text=True, env=env, check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout

    # Upstream wins, shadow is NOT applied
    upa = (out / "wiki" / "tickers" / "UPA" / "overview.md").read_text(encoding="utf-8")
    assert "Shadow" not in upa
    assert "Upstream fixture ticker A" in upa
    assert frontmatter.loads(upa).get("source") == "upstream"
