import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "merge_log.py"


def run_script(upstream, overlay, output):
    return subprocess.run(
        [sys.executable, str(SCRIPT),
         "--upstream", str(upstream),
         "--overlay", str(overlay),
         "--output", str(output)],
        capture_output=True, text=True, check=False,
    )


def test_merges_and_sorts_by_timestamp(tmp_path):
    up = tmp_path / "up.md"
    ov = tmp_path / "ov.md"
    out = tmp_path / "out.md"
    up.write_text(
        "# Upstream Log\n\n"
        "```\n"
        "LOG 2026-04-05 12:00 INGEST BKNG — thesis compiled\n"
        "LOG 2026-04-17 14:00 INGEST SCHW — Q1 2026 earnings\n"
        "```\n",
        encoding="utf-8",
    )
    ov.write_text(
        "LOG 2026-04-10 09:00 INGEST NVTS — overlay ticker added\n"
        "LOG 2026-04-22 22:40 INGEST chen-yun — imported chen timeline\n",
        encoding="utf-8",
    )
    r = run_script(up, ov, out)
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")

    assert "BKNG" in text and "SCHW" in text and "NVTS" in text and "chen-yun" in text

    i_bkng = text.index("BKNG")
    i_nvts = text.index("NVTS")
    i_schw = text.index("SCHW")
    i_chen = text.index("chen-yun")
    assert i_bkng < i_nvts < i_schw < i_chen

    assert text.count("```") == 2


def test_handles_missing_overlay_log(tmp_path):
    up = tmp_path / "up.md"
    out = tmp_path / "out.md"
    up.write_text(
        "```\nLOG 2026-04-05 12:00 INGEST BKNG — x\n```\n",
        encoding="utf-8",
    )
    r = run_script(up, tmp_path / "nonexistent.md", out)
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")
    assert "BKNG" in text
    assert text.count("```") == 2


def test_ignores_non_log_lines_in_upstream(tmp_path):
    up = tmp_path / "up.md"
    ov = tmp_path / "ov.md"
    out = tmp_path / "out.md"
    up.write_text(
        "# Upstream Log\n\n"
        "Introductory paragraph that should not be emitted.\n\n"
        "```\n"
        "LOG 2026-04-05 12:00 INGEST BKNG — x\n"
        "```\n",
        encoding="utf-8",
    )
    ov.write_text("LOG 2026-04-10 09:00 INGEST NVTS — y\n", encoding="utf-8")
    r = run_script(up, ov, out)
    assert r.returncode == 0
    text = out.read_text(encoding="utf-8")
    assert "Introductory paragraph" not in text
    assert "BKNG" in text and "NVTS" in text
