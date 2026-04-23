import subprocess
import sys
from pathlib import Path
import frontmatter

SCRIPT = Path(__file__).parent.parent / "scripts" / "inject_frontmatter.py"


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, check=False,
    )


def test_injects_source_when_missing(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("# Hello\n\nBody text.\n", encoding="utf-8")
    r = run("--source", "upstream", str(f))
    assert r.returncode == 0, r.stderr
    post = frontmatter.loads(f.read_text(encoding="utf-8"))
    assert post.get("source") == "upstream"
    assert "Hello" in post.content


def test_idempotent_keeps_existing_source(tmp_path):
    f = tmp_path / "b.md"
    f.write_text("---\nsource: upstream\n---\n# Hi\n", encoding="utf-8")
    r = run("--source", "austin", str(f))
    assert r.returncode == 0
    post = frontmatter.loads(f.read_text(encoding="utf-8"))
    assert post.get("source") == "upstream"


def test_preserves_other_frontmatter_keys(tmp_path):
    f = tmp_path / "c.md"
    f.write_text("---\nticker: BKNG\nupdated: 2026-04-05\n---\n# Content\n", encoding="utf-8")
    r = run("--source", "upstream", str(f))
    assert r.returncode == 0
    post = frontmatter.loads(f.read_text(encoding="utf-8"))
    assert post.get("ticker") == "BKNG"
    assert post.get("source") == "upstream"


def test_accepts_multiple_paths(tmp_path):
    a = tmp_path / "x.md"
    b = tmp_path / "y.md"
    a.write_text("# A\n", encoding="utf-8")
    b.write_text("# B\n", encoding="utf-8")
    r = run("--source", "austin", str(a), str(b))
    assert r.returncode == 0
    assert frontmatter.loads(a.read_text(encoding="utf-8")).get("source") == "austin"
    assert frontmatter.loads(b.read_text(encoding="utf-8")).get("source") == "austin"
