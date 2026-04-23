import subprocess
import sys
from pathlib import Path
import shutil

SCRIPT = Path(__file__).parent.parent / "scripts" / "gen_watchlist.py"
FIXTURE = Path(__file__).parent / "fixtures" / "sample_tickers"


def run_script(wiki_root, output, lang="en"):
    return subprocess.run(
        [sys.executable, str(SCRIPT),
         "--wiki-root", str(wiki_root),
         "--output", str(output),
         "--lang", lang],
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


def test_multiline_status_is_joined_not_truncated(tmp_path):
    """Regression: the Status value can span multiple lines (wrapped markdown).
    The earlier regex captured only the first line, producing truncated cells
    like `NEW — Speculative turnaround with negative expected return at`
    (missing the rest). Both lines must collapse into one cell."""
    wiki = tmp_path / "wiki"
    (wiki / "tickers" / "MULTI").mkdir(parents=True)
    (wiki / "tickers" / "MULTI" / "overview.md").write_text(
        "---\nsource: austin\nticker: MULTI\n---\n# MULTI\n",
        encoding="utf-8",
    )
    (wiki / "tickers" / "MULTI" / "changelog.md").write_text(
        "## [2026-04-22] — Initial\n\n"
        "### Thesis Status\n"
        "- **Overall**: NEW — Speculative turnaround with negative expected return at\n"
        "  current price per wiki framework\n"
        "- **Moat**: Narrow\n\n"
        "### Action\n"
        "- [x] **Watch** — Await Q1 2026 earnings (May 5, 2026) AND/OR pullback to below\n"
        "  PW EV ($15.35) before any position build\n\n"
        "**Next review trigger**: Q1 2026 earnings (May 5, 2026) OR any NVIDIA revenue\n"
        "guidance / customer-win announcement\n",
        encoding="utf-8",
    )
    out = tmp_path / "watchlist.md"
    r = run_script(wiki, out)
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")

    # The trailing continuation fragment must be present — this would have
    # been truncated by the old regex.
    assert "current price per wiki framework" in text
    assert "before any position build" in text
    assert "customer-win announcement" in text
    # The status line must NOT have been cut at the " at" word wrap.
    assert "negative expected return at |" not in text


def test_parses_chinese_changelog_with_fullwidth_colon_and_double_emdash(tmp_path):
    """zh mode: Chinese changelog uses `- **总体**：...` (full-width colon)
    and `- [x] **观察** —— ...` (double em-dash). Both must parse."""
    wiki = tmp_path / "wiki"
    (wiki / "tickers" / "ZHTK").mkdir(parents=True)
    (wiki / "tickers" / "ZHTK" / "overview.md").write_text(
        "---\nsource: austin\nticker: ZHTK\n---\n# ZHTK\n",
        encoding="utf-8",
    )
    (wiki / "tickers" / "ZHTK" / "changelog.zh.md").write_text(
        "## [2026-04-22] —— 初版论文\n\n"
        "### 论文状态\n"
        "- **总体**：新建 —— 投机转型股，当前价位为负预期回报\n"
        "- **护城河**：窄 / 有争议\n\n"
        "### 行动\n"
        "- [x] **观察** —— 等待 Q1 2026 财报或回调至 PW EV 以下再建仓\n\n"
        "**下次审阅触发**：Q1 2026 财报（2026-05-05）\n",
        encoding="utf-8",
    )
    out = tmp_path / "watchlist.zh.md"
    r = run_script(wiki, out, lang="zh")
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")

    # Localized table headers
    assert "| Ticker | 来源 | 最新 | 状态 | 操作 | 下次复核 |" in text
    # Chinese field content correctly parsed
    assert "新建 —— 投机转型股" in text
    assert "观察" in text and "等待 Q1 2026 财报" in text
    assert "Q1 2026 财报（2026-05-05）" in text


def test_zh_mode_falls_back_to_en_changelog_when_zh_missing(tmp_path):
    """Upstream tickers don't have changelog.zh.md. zh mode must still emit
    a row for them by reading changelog.md."""
    wiki = tmp_path / "wiki"
    (wiki / "tickers" / "UPSR").mkdir(parents=True)
    (wiki / "tickers" / "UPSR" / "overview.md").write_text(
        "---\nsource: upstream\nticker: UPSR\n---\n# UPSR\n",
        encoding="utf-8",
    )
    (wiki / "tickers" / "UPSR" / "changelog.md").write_text(
        "## 2026-04-05 — Initial\n\n"
        "### Thesis Status\n- **Overall**: Strengthened\n\n"
        "### Action\n- [x] Hold — baseline\n\n"
        "**Next review trigger**: Q1 2026 earnings\n",
        encoding="utf-8",
    )
    out = tmp_path / "watchlist.zh.md"
    r = run_script(wiki, out, lang="zh")
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")
    assert "UPSR" in text
    assert "Strengthened" in text  # English content retained


def test_pipe_char_in_value_is_escaped_to_slash(tmp_path):
    """Pipe characters would break the markdown table row. Sanitize to /."""
    wiki = tmp_path / "wiki"
    (wiki / "tickers" / "PIPE").mkdir(parents=True)
    (wiki / "tickers" / "PIPE" / "overview.md").write_text(
        "---\nsource: austin\nticker: PIPE\n---\n# PIPE\n",
        encoding="utf-8",
    )
    (wiki / "tickers" / "PIPE" / "changelog.md").write_text(
        "## [2026-04-22] — X\n\n"
        "- **Overall**: A | B | C\n\n"
        "- [x] Hold — sample | with pipes\n\n"
        "**Next review trigger**: review\n",
        encoding="utf-8",
    )
    out = tmp_path / "watchlist.md"
    r = run_script(wiki, out)
    assert r.returncode == 0, r.stderr
    text = out.read_text(encoding="utf-8")
    assert "A / B / C" in text
    # Raw pipes must not appear in the data cells (they appear only as
    # table-row delimiters).
    data_lines = [l for l in text.splitlines() if l.startswith("| PIPE")]
    assert len(data_lines) == 1
    # Exactly 7 pipe chars on a row (6 cell separators + outer + outer).
    assert data_lines[0].count("|") == 7


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
