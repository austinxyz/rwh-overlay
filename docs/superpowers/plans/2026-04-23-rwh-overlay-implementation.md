# rwh-overlay Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a read-only upstream mirror (`personal/rwh`) + private overlay repo (`austinxyz/rwh-overlay`) + deterministic build pipeline producing a unified stock KB under `personal/stock-kb/` for Syncthing → NAS → Quartz.

**Architecture:** Three sibling directories on disk. A pure-Python build script (`build_stock_kb.py`) merges upstream and overlay trees via `shutil.copytree` with "skip if destination exists" semantics for the overlay pass, tags source via frontmatter, and generates derived index/watchlist/log. Upstream stays pristine via a pre-commit hook guard; overlay is a normal git repo; stock-kb is an untracked build artifact.

**Tech Stack:** Python 3.14 (via `py` launcher on Windows), `python-frontmatter`, `pytest` (dev), git. Build orchestrator is pure Python (`shutil` / `pathlib`) — no rsync or bash dependency (changed from the original spec after rsync install via Scoop failed on Windows).

**Spec Reference:** `docs/superpowers/specs/2026-04-23-rwh-overlay-architecture-design.md`

---

## Phase 0: Preflight

### Task 1: Verify Python and create overlay GitHub repo

**Files:** none (environment + remote setup)

Note: earlier drafts required installing `rsync` via Scoop, but Scoop's `main`
bucket didn't expose it reliably on this Windows machine. Build orchestrator
was rewritten in pure Python (see Task 8), so rsync is no longer needed.

- [ ] **Step 1: Verify Python toolchain**

```bash
py --version
py -m pip --version
```

Expected: `Python 3.14.3` (or later) and a `pip` line.

- [ ] **Step 2: Create empty private GitHub repo `austinxyz/rwh-overlay`**

In browser: github.com/new → name `rwh-overlay`, visibility Private, no README/gitignore/license. Copy the SSH clone URL (e.g., `git@github.com:austinxyz/rwh-overlay.git`).

- [ ] **Step 3: Verify GitHub access**

```bash
ssh -T git@github.com
```

Expected: `Hi austinxyz! You've successfully authenticated...`

---

## Phase 1: Overlay Scaffolding and Build Pipeline

### Task 2: Initialize overlay repo and directory layout

**Files:**
- Create: `~/projects/personal/rwh-overlay/` (root)
- Create: `~/projects/personal/rwh-overlay/wiki/tickers/.gitkeep`
- Create: `~/projects/personal/rwh-overlay/wiki/opinions/.gitkeep`
- Create: `~/projects/personal/rwh-overlay/raw/analyses/.gitkeep`
- Create: `~/projects/personal/rwh-overlay/scripts/.gitkeep`
- Create: `~/projects/personal/rwh-overlay/tests/fixtures/.gitkeep`
- Create: `~/projects/personal/rwh-overlay/docs/superpowers/{specs,plans}/.gitkeep`

- [ ] **Step 1: Create root directory + git init**

```bash
mkdir -p ~/projects/personal/rwh-overlay
cd ~/projects/personal/rwh-overlay
git init -b main
git remote add origin git@github.com:austinxyz/rwh-overlay.git
```

- [ ] **Step 2: Create the skeleton directory tree**

```bash
mkdir -p wiki/tickers wiki/opinions raw/analyses scripts tests/fixtures/mock_upstream/wiki/tickers tests/fixtures/mock_overlay/wiki/tickers docs/superpowers/specs docs/superpowers/plans
touch wiki/tickers/.gitkeep wiki/opinions/.gitkeep raw/analyses/.gitkeep scripts/.gitkeep tests/fixtures/.gitkeep docs/superpowers/specs/.gitkeep docs/superpowers/plans/.gitkeep
```

- [ ] **Step 3: Verify tree**

```bash
find . -type d -not -path './.git*' | sort
```

Expected output (order may vary):

```
.
./docs
./docs/superpowers
./docs/superpowers/plans
./docs/superpowers/specs
./raw
./raw/analyses
./scripts
./tests
./tests/fixtures
./tests/fixtures/mock_overlay
./tests/fixtures/mock_overlay/wiki
./tests/fixtures/mock_overlay/wiki/tickers
./tests/fixtures/mock_upstream
./tests/fixtures/mock_upstream/wiki
./tests/fixtures/mock_upstream/wiki/tickers
./wiki
./wiki/opinions
./wiki/tickers
```

- [ ] **Step 4: Do NOT commit yet** — we'll batch-commit at end of Phase 1.

### Task 3: Set up Python dev environment

**Files:**
- Create: `~/projects/personal/rwh-overlay/requirements-dev.txt`
- Create: `~/projects/personal/rwh-overlay/.venv/` (gitignored)

- [ ] **Step 1: Write `requirements-dev.txt`**

```
python-frontmatter==1.1.0
pyyaml==6.0.2
pytest==8.3.4
```

- [ ] **Step 2: Create venv and install**

```bash
cd ~/projects/personal/rwh-overlay
py -m venv .venv
source .venv/Scripts/activate
pip install -r requirements-dev.txt
```

- [ ] **Step 3: Verify imports**

```bash
python -c "import frontmatter, yaml, pytest; print('OK')"
```

Expected: `OK`.

### Task 4: Write `inject_frontmatter.py` (TDD)

**Files:**
- Create: `scripts/inject_frontmatter.py`
- Create: `tests/test_inject_frontmatter.py`

- [ ] **Step 1: Write the failing test**

`tests/test_inject_frontmatter.py`:

```python
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
    assert post.get("source") == "upstream"  # unchanged


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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/projects/personal/rwh-overlay
source .venv/Scripts/activate
pytest tests/test_inject_frontmatter.py -v
```

Expected: 4 failures — script doesn't exist.

- [ ] **Step 3: Write the implementation**

`scripts/inject_frontmatter.py`:

```python
#!/usr/bin/env python3
"""Inject a `source` frontmatter key into one or more markdown files.

Idempotent: if `source:` is already set, the file is untouched.
"""
import argparse
import sys
from pathlib import Path

import frontmatter


def inject(path: Path, source: str) -> bool:
    """Return True if the file was modified, False if skipped."""
    text = path.read_text(encoding="utf-8")
    post = frontmatter.loads(text)
    if post.get("source"):
        return False
    post["source"] = source
    path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True,
                    choices=["upstream", "austin", "austin-observation"])
    ap.add_argument("paths", nargs="+", type=Path)
    args = ap.parse_args()

    for p in args.paths:
        if not p.is_file():
            print(f"skip (not a file): {p}", file=sys.stderr)
            continue
        if p.suffix != ".md":
            continue
        if inject(p, args.source):
            print(f"tagged {args.source}: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_inject_frontmatter.py -v
```

Expected: 4 passed.

### Task 5: Write `gen_index.py` (TDD)

**Files:**
- Create: `scripts/gen_index.py`
- Create: `tests/test_gen_index.py`
- Create: `tests/fixtures/sample_tickers/UPS_A/overview.md` (test fixture)

- [ ] **Step 1: Create the fixture**

```bash
mkdir -p tests/fixtures/sample_tickers/{UPS_A,AUS_B,UPS_C}
```

`tests/fixtures/sample_tickers/UPS_A/overview.md`:

```markdown
---
source: upstream
ticker: UPS_A
summary: Fake upstream ticker A for index tests.
updated: 2026-04-10
---

# UPS_A Overview
```

`tests/fixtures/sample_tickers/AUS_B/overview.md`:

```markdown
---
source: austin
ticker: AUS_B
summary: Fake austin ticker B for index tests.
updated: 2026-04-22
---

# AUS_B Overview
```

`tests/fixtures/sample_tickers/UPS_C/overview.md`:

```markdown
---
source: upstream
ticker: UPS_C
summary: Fake upstream ticker C.
updated: 2026-04-01
---

# UPS_C Overview
```

- [ ] **Step 2: Write the failing test**

`tests/test_gen_index.py`:

```python
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

    # Two section headings
    assert "## Upstream Tickers" in text
    assert "## My Tickers" in text
    # Upstream tickers are sorted alphabetically
    ups_a = text.index("UPS_A")
    ups_c = text.index("UPS_C")
    assert ups_a < ups_c
    # Austin ticker in its own section (after Upstream)
    aus_b = text.index("AUS_B")
    my_heading = text.index("## My Tickers")
    assert aus_b > my_heading
    # Summaries and updated dates included
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
```

- [ ] **Step 3: Run tests — should fail**

```bash
pytest tests/test_gen_index.py -v
```

Expected: 2 failures, script missing.

- [ ] **Step 4: Write the implementation**

`scripts/gen_index.py`:

```python
#!/usr/bin/env python3
"""Generate wiki/index.md by scanning tickers/*/overview.md frontmatter."""
import argparse
import sys
from pathlib import Path

import frontmatter


def collect(wiki_root: Path):
    rows = {"upstream": [], "austin": []}
    tickers_dir = wiki_root / "tickers"
    if not tickers_dir.is_dir():
        return rows
    for ticker_dir in sorted(tickers_dir.iterdir()):
        overview = ticker_dir / "overview.md"
        if not overview.is_file():
            continue
        post = frontmatter.loads(overview.read_text(encoding="utf-8"))
        src = post.get("source", "unknown")
        if src not in rows:
            continue
        rows[src].append({
            "ticker": post.get("ticker", ticker_dir.name),
            "summary": post.get("summary", ""),
            "updated": post.get("updated", ""),
            "path": f"tickers/{ticker_dir.name}/overview.md",
        })
    return rows


def render_table(rows):
    if not rows:
        return "_(none)_\n"
    lines = [
        "| Ticker | Summary | Updated |",
        "|--------|---------|---------|",
    ]
    for r in rows:
        lines.append(f"| [{r['ticker']}]({r['path']}) | {r['summary']} | {r['updated']} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wiki-root", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    rows = collect(args.wiki_root)

    out = []
    out.append("# Ticker Index\n")
    out.append("*Auto-generated by `scripts/gen_index.py`. Do not edit by hand.*\n")
    out.append("## Upstream Tickers\n")
    out.append(render_table(rows["upstream"]))
    out.append("## My Tickers\n")
    out.append(render_table(rows["austin"]))
    args.output.write_text("\n".join(out), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run tests — should pass**

```bash
pytest tests/test_gen_index.py -v
```

Expected: 2 passed.

### Task 6: Write `gen_watchlist.py` (TDD)

**Files:**
- Create: `scripts/gen_watchlist.py`
- Create: `tests/test_gen_watchlist.py`
- Create: `tests/fixtures/sample_tickers/UPS_A/changelog.md` (extend fixture)
- Create: `tests/fixtures/sample_tickers/AUS_B/changelog.md`

- [ ] **Step 1: Extend the fixture with changelogs**

`tests/fixtures/sample_tickers/UPS_A/changelog.md`:

```markdown
## [2026-04-10] — Earnings Q1

**Trigger**: Q1 2026 earnings
**Data points reviewed**: transcript, 10-Q

### What Changed
- Revenue beat +8%

### Thesis Status
- **Overall**: Strengthened
- **BAIT delta**: B+A strengthened
- **Price target delta**: Bull $200 → $220 | Base $150 → $160 | Bear $100 → $110

### Action
- [x] Buy more — starter tranche
- [ ] Trim
- [ ] Hold
- [ ] Watch

**Next review trigger**: Q2 2026 earnings
```

`tests/fixtures/sample_tickers/AUS_B/changelog.md`:

```markdown
## [2026-04-22] — Promotion from opinions

**Trigger**: Promoted from chen-yun observations
**Data points reviewed**: 10-K, recent PR

### What Changed
- Initial thesis built

### Thesis Status
- **Overall**: Unchanged
- **BAIT delta**: Weak
- **Price target delta**: Bull $30 (25%) + Base $13 (45%) + Bear $5 (30%) = $15.35

### Action
- [ ] Buy more
- [ ] Trim
- [ ] Hold
- [x] Watch — avoid new entries at current price

**Next review trigger**: Q1 2026 earnings May 5, 2026
```

- [ ] **Step 2: Write the failing test**

`tests/test_gen_watchlist.py`:

```python
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

    # Ticker column
    assert "UPS_A" in text
    assert "AUS_B" in text
    # Action extracted from [x] line
    assert "Buy more" in text
    assert "Watch" in text
    # Thesis status
    assert "Strengthened" in text
    # Next review
    assert "Q2 2026 earnings" in text or "May 5, 2026" in text


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
```

- [ ] **Step 3: Run tests — should fail**

```bash
pytest tests/test_gen_watchlist.py -v
```

Expected: 2 failures, script missing.

- [ ] **Step 4: Write the implementation**

`scripts/gen_watchlist.py`:

```python
#!/usr/bin/env python3
"""Generate wiki/watchlist.md by scanning each ticker's latest changelog entry."""
import argparse
import re
import sys
from pathlib import Path

import frontmatter

HEADING_RE = re.compile(r"^##\s*\[(?P<date>\d{4}-\d{2}-\d{2})\]\s*—\s*(?P<title>.+)$")
THESIS_STATUS_RE = re.compile(r"^\s*-\s*\*\*Overall\*\*:\s*(?P<status>.+)$")
CHECKED_ACTION_RE = re.compile(r"^\s*-\s*\[x\]\s*(?P<action>[^—\-\n]+?)(?:\s*—\s*(?P<detail>.+))?$")
NEXT_REVIEW_RE = re.compile(r"^\s*\*\*Next review trigger\*\*:\s*(?P<trigger>.+)$")


def parse_latest_entry(changelog_path: Path):
    if not changelog_path.is_file():
        return None
    text = changelog_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    latest = None
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m:
            latest = {"date": m.group("date"), "title": m.group("title"),
                      "start": i, "status": "", "action": "", "next_review": ""}
            break
    if not latest:
        return None
    # Scan until next ## heading or EOF
    j = latest["start"] + 1
    while j < len(lines) and not lines[j].startswith("## "):
        line = lines[j]
        m = THESIS_STATUS_RE.match(line)
        if m and not latest["status"]:
            latest["status"] = m.group("status").strip()
        m = CHECKED_ACTION_RE.match(line)
        if m and not latest["action"]:
            action = m.group("action").strip()
            detail = (m.group("detail") or "").strip()
            latest["action"] = f"{action} — {detail}" if detail else action
        m = NEXT_REVIEW_RE.match(line)
        if m and not latest["next_review"]:
            latest["next_review"] = m.group("trigger").strip()
        j += 1
    return latest


def collect(wiki_root: Path):
    rows = []
    tickers_dir = wiki_root / "tickers"
    if not tickers_dir.is_dir():
        return rows
    for ticker_dir in sorted(tickers_dir.iterdir()):
        overview = ticker_dir / "overview.md"
        if not overview.is_file():
            continue
        post = frontmatter.loads(overview.read_text(encoding="utf-8"))
        entry = parse_latest_entry(ticker_dir / "changelog.md")
        rows.append({
            "ticker": post.get("ticker", ticker_dir.name),
            "source": post.get("source", ""),
            "date": entry["date"] if entry else "",
            "status": entry["status"] if entry else "_(no changelog)_",
            "action": entry["action"] if entry else "_(no changelog)_",
            "next_review": entry["next_review"] if entry else "",
        })
    return rows


def render(rows):
    lines = [
        "# Watchlist — Cross-Ticker Ranking\n",
        "*Auto-generated by `scripts/gen_watchlist.py`. Do not edit by hand.*\n",
        "| Ticker | Source | Latest | Status | Action | Next Review |",
        "|--------|--------|--------|--------|--------|-------------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['ticker']} | {r['source']} | {r['date']} | {r['status']} | {r['action']} | {r['next_review']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wiki-root", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    rows = collect(args.wiki_root)
    args.output.write_text(render(rows), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run tests — should pass**

```bash
pytest tests/test_gen_watchlist.py -v
```

Expected: 2 passed.

### Task 7: Write `merge_log.py` (TDD)

**Files:**
- Create: `scripts/merge_log.py`
- Create: `tests/test_merge_log.py`

- [ ] **Step 1: Write the failing test**

`tests/test_merge_log.py`:

```python
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

    # All 4 entries present
    assert "BKNG" in text and "SCHW" in text and "NVTS" in text and "chen-yun" in text

    # Sorted: 04-05 < 04-10 < 04-17 < 04-22
    i_bkng = text.index("BKNG")
    i_nvts = text.index("NVTS")
    i_schw = text.index("SCHW")
    i_chen = text.index("chen-yun")
    assert i_bkng < i_nvts < i_schw < i_chen

    # Wrapped in exactly one fence (two triple-backticks total)
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
```

- [ ] **Step 2: Run tests — should fail**

```bash
pytest tests/test_merge_log.py -v
```

Expected: 3 failures, script missing.

- [ ] **Step 3: Write the implementation**

`scripts/merge_log.py`:

```python
#!/usr/bin/env python3
"""Merge upstream log.md and overlay overlay-log.md into a single fenced log.

Extracts lines matching `LOG YYYY-MM-DD HH:MM ...` from both inputs,
sorts by timestamp, and wraps the result in a single fenced code block
to preserve per-line rendering (per CLAUDE.md).
"""
import argparse
import re
import sys
from pathlib import Path

LOG_LINE_RE = re.compile(r"^LOG\s+(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s+")


def extract_log_lines(path: Path):
    if not path.is_file():
        return []
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = LOG_LINE_RE.match(line)
        if m:
            lines.append((m.group("ts"), line))
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--upstream", required=True, type=Path)
    ap.add_argument("--overlay", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    entries = extract_log_lines(args.upstream) + extract_log_lines(args.overlay)
    entries.sort(key=lambda p: p[0])

    out_lines = [
        "# Operation Log",
        "",
        "*Auto-generated by `scripts/merge_log.py`. Append new entries to"
        " `overlay-log.md` in the overlay repo.*",
        "",
        "```",
    ]
    out_lines.extend(line for _, line in entries)
    out_lines.append("```")
    out_lines.append("")
    args.output.write_text("\n".join(out_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests — should pass**

```bash
pytest tests/test_merge_log.py -v
```

Expected: 3 passed.

### Task 8: Write `build_stock_kb.py` orchestrator (pure Python)

**Files:**
- Create: `scripts/build_stock_kb.py`

- [ ] **Step 1: Write the orchestrator**

`scripts/build_stock_kb.py`:

```python
#!/usr/bin/env python3
"""Build the merged stock knowledge base from upstream (rwh) + overlay.

Pure-Python replacement for the original bash+rsync design (rsync was not
available on the user's Windows environment).

Env vars (with CLI-flag overrides):
  RWH_DIR      path to kgajjala/rwh clone           (default: ../rwh)
  OVERLAY_DIR  path to rwh-overlay clone            (default: this file's repo root)
  OUTPUT_DIR   path to emit the merged KB           (default: ../stock-kb)
  SKIP_PULL    if set, skip `git pull` on RWH_DIR   (useful in tests)
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# Derived files are regenerated; never copy them from sources.
DERIVED_FILES = {"index.md", "watchlist.md", "log.md"}


def env_path(name: str, default: Path) -> Path:
    val = os.environ.get(name)
    return Path(val).resolve() if val else default.resolve()


def preflight(rwh: Path, overlay: Path) -> None:
    if not (rwh / "wiki").is_dir():
        sys.exit(f"❌ RWH_DIR={rwh} does not contain wiki/")
    if not (overlay / "wiki").is_dir():
        sys.exit(f"❌ OVERLAY_DIR={overlay} does not contain wiki/")


def git_pull(rwh: Path) -> None:
    print("⬇️  Pulling upstream (fast-forward only)...")
    subprocess.run(
        ["git", "-C", str(rwh), "pull", "--ff-only", "origin", "main"],
        check=True,
    )


def clean_output(output: Path) -> None:
    print(f"🧹 Cleaning {output}/wiki/...")
    if (output / "wiki").exists():
        shutil.rmtree(output / "wiki")
    (output / "wiki").mkdir(parents=True)
    (output / "raw").mkdir(parents=True, exist_ok=True)


def copy_tree_excluding_derived(src: Path, dst: Path) -> None:
    """Copy `src` → `dst` recursively, skipping index.md/watchlist.md/log.md at any depth."""
    for root, _dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for name in files:
            if name in DERIVED_FILES:
                continue
            shutil.copy2(Path(root) / name, dst / rel / name)


def overlay_copy_with_skip(overlay_wiki: Path, output_wiki: Path) -> tuple[list[Path], list[Path]]:
    """Walk overlay/wiki; copy files only if destination is missing. Return (copied_relpaths, skipped_relpaths)."""
    copied: list[Path] = []
    skipped: list[Path] = []
    for root, _dirs, files in os.walk(overlay_wiki):
        rel_dir = Path(root).relative_to(overlay_wiki)
        (output_wiki / rel_dir).mkdir(parents=True, exist_ok=True)
        for name in files:
            if name in DERIVED_FILES:
                continue
            rel = rel_dir / name
            src = Path(root) / name
            dst = output_wiki / rel
            if dst.exists():
                skipped.append(rel)
            else:
                shutil.copy2(src, dst)
                copied.append(rel)
    return copied, skipped


def run_injector(py: str, paths: list[Path], source: str) -> None:
    """Invoke inject_frontmatter.py with many paths in a single subprocess."""
    if not paths:
        return
    cmd = [py, str(SCRIPT_DIR / "inject_frontmatter.py"), "--source", source] + [str(p) for p in paths]
    subprocess.run(cmd, check=True)


def tag_all_upstream(py: str, output_wiki: Path) -> None:
    paths = [p for p in output_wiki.rglob("*.md")]
    print(f"🏷️  Tagging {len(paths)} upstream files (source: upstream)...")
    run_injector(py, paths, "upstream")


def tag_overlay_copies(py: str, output_wiki: Path, copied: list[Path]) -> None:
    """Tag files that were freshly copied from the overlay (not shadowed)."""
    austin, observation = [], []
    for rel in copied:
        if rel.suffix != ".md":
            continue
        abs_path = output_wiki / rel
        if not abs_path.is_file():
            continue
        if rel.parts and rel.parts[0] == "opinions":
            observation.append(abs_path)
        else:
            austin.append(abs_path)
    print(f"🏷️  Tagging {len(austin)} overlay files as austin and {len(observation)} as austin-observation...")
    run_injector(py, austin, "austin")
    run_injector(py, observation, "austin-observation")


def copy_raw(overlay: Path, output: Path) -> None:
    if not (overlay / "raw").is_dir():
        return
    print("📋 Copying overlay raw/...")
    shutil.copytree(overlay / "raw", output / "raw", dirs_exist_ok=True)


def copy_claude(rwh: Path, overlay: Path, output: Path) -> None:
    print("📋 Copying CLAUDE instructions...")
    up = rwh / "CLAUDE.md"
    if up.is_file():
        shutil.copy2(up, output / "CLAUDE.upstream.md")
    ov = overlay / "CLAUDE.overlay.md"
    if ov.is_file():
        shutil.copy2(ov, output / "CLAUDE.overlay.md")


def generate_derived(py: str, rwh: Path, overlay: Path, output: Path) -> None:
    print("🧮 Generating index.md...")
    subprocess.run([py, str(SCRIPT_DIR / "gen_index.py"),
                    "--wiki-root", str(output / "wiki"),
                    "--output", str(output / "wiki" / "index.md")], check=True)
    print("🧮 Generating watchlist.md...")
    subprocess.run([py, str(SCRIPT_DIR / "gen_watchlist.py"),
                    "--wiki-root", str(output / "wiki"),
                    "--output", str(output / "wiki" / "watchlist.md")], check=True)
    print("🧮 Merging log.md...")
    subprocess.run([py, str(SCRIPT_DIR / "merge_log.py"),
                    "--upstream", str(rwh / "wiki" / "log.md"),
                    "--overlay",  str(overlay / "overlay-log.md"),
                    "--output",   str(output / "wiki" / "log.md")], check=True)


def main() -> int:
    repo_root = SCRIPT_DIR.parent
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rwh-dir", type=Path, default=None)
    ap.add_argument("--overlay-dir", type=Path, default=None)
    ap.add_argument("--output-dir", type=Path, default=None)
    ap.add_argument("--skip-pull", action="store_true", default=False)
    args = ap.parse_args()

    rwh = (args.rwh_dir or env_path("RWH_DIR", repo_root.parent / "rwh")).resolve()
    overlay = (args.overlay_dir or env_path("OVERLAY_DIR", repo_root)).resolve()
    output = (args.output_dir or env_path("OUTPUT_DIR", repo_root.parent / "stock-kb")).resolve()
    skip_pull = args.skip_pull or bool(os.environ.get("SKIP_PULL"))

    print(f"📂 RWH_DIR      = {rwh}")
    print(f"📂 OVERLAY_DIR  = {overlay}")
    print(f"📂 OUTPUT_DIR   = {output}")

    preflight(rwh, overlay)

    # Pick a Python interpreter for invoking helper scripts.
    py = sys.executable

    if not skip_pull:
        git_pull(rwh)

    clean_output(output)
    print("📋 Copying upstream wiki/ (excluding derived files)...")
    copy_tree_excluding_derived(rwh / "wiki", output / "wiki")
    tag_all_upstream(py, output / "wiki")

    print("📋 Copying overlay wiki/ (skipping files that shadow upstream)...")
    copied, shadowed = overlay_copy_with_skip(overlay / "wiki", output / "wiki")
    tag_overlay_copies(py, output / "wiki", copied)

    copy_raw(overlay, output)
    copy_claude(rwh, overlay, output)
    generate_derived(py, rwh, overlay, output)

    ticker_count = sum(1 for p in (output / "wiki" / "tickers").iterdir() if p.is_dir()) \
        if (output / "wiki" / "tickers").is_dir() else 0
    print("✅ Build complete.")
    print(f"   Total tickers:  {ticker_count}")
    print(f"   Output:         {output}")
    if shadowed:
        print(f"⚠️  Overlay files shadowed by upstream (kept upstream, skipped overlay):")
        for rel in shadowed:
            print(f"     - {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Verify the file parses as valid Python**

```bash
cd ~/projects/personal/rwh-overlay
py -c "import ast, pathlib; ast.parse(pathlib.Path('scripts/build_stock_kb.py').read_text(encoding='utf-8')); print('OK')"
```

Expected: `OK`. Execution test comes in Task 9.

### Task 9: Integration test `build_stock_kb.py` with fixture dirs

**Files:**
- Create: `tests/fixtures/mock_upstream/` (full tree)
- Create: `tests/fixtures/mock_overlay/` (full tree)
- Create: `tests/test_build_integration.py`

- [ ] **Step 1: Populate mock_upstream fixture**

```bash
mkdir -p tests/fixtures/mock_upstream/wiki/tickers/UPA tests/fixtures/mock_upstream/wiki/frameworks
```

`tests/fixtures/mock_upstream/CLAUDE.md`:

```markdown
# Upstream CLAUDE

Framework lives here.
```

`tests/fixtures/mock_upstream/wiki/tickers/UPA/overview.md`:

```markdown
---
ticker: UPA
summary: Upstream fixture ticker A.
updated: 2026-04-10
---

# UPA Overview
```

`tests/fixtures/mock_upstream/wiki/tickers/UPA/changelog.md`:

```markdown
## [2026-04-10] — Initial

### Thesis Status
- **Overall**: Unchanged

### Action
- [x] Hold — baseline

**Next review trigger**: Q2 2026
```

`tests/fixtures/mock_upstream/wiki/frameworks/bait.md`:

```markdown
# BAIT Framework
Upstream framework content.
```

`tests/fixtures/mock_upstream/wiki/log.md`:

````markdown
# Upstream Log

```
LOG 2026-04-10 12:00 INGEST UPA — fixture upstream entry
```
````

Note: this is a raw file on disk — the outer ```` is markdown rendering of the inner ``` fence. On disk the file should literally contain the ``` fenced entry; create with:

```bash
cat > tests/fixtures/mock_upstream/wiki/log.md <<'EOF'
# Upstream Log

```
LOG 2026-04-10 12:00 INGEST UPA — fixture upstream entry
```
EOF
```

- [ ] **Step 2: Populate mock_overlay fixture**

```bash
mkdir -p tests/fixtures/mock_overlay/wiki/tickers/AUB tests/fixtures/mock_overlay/wiki/opinions
```

`tests/fixtures/mock_overlay/CLAUDE.overlay.md`:

```markdown
# Overlay CLAUDE

Overlay-specific extension rules.
```

`tests/fixtures/mock_overlay/wiki/tickers/AUB/overview.md`:

```markdown
---
ticker: AUB
summary: Overlay fixture ticker B.
updated: 2026-04-22
---

# AUB Overview
```

`tests/fixtures/mock_overlay/wiki/tickers/AUB/changelog.md`:

```markdown
## [2026-04-22] — Added

### Thesis Status
- **Overall**: Unchanged

### Action
- [x] Watch — speculative

**Next review trigger**: Q1 2026 earnings
```

`tests/fixtures/mock_overlay/wiki/opinions/fake-source.md`:

```markdown
---
summary: Fake third-party opinion fixture.
---

# Fake Source Opinions
```

`tests/fixtures/mock_overlay/overlay-log.md`:

```
LOG 2026-04-22 22:00 INGEST AUB — overlay fixture entry
```

- [ ] **Step 3: Write the integration test**

`tests/test_build_integration.py`:

```python
import os
import shutil
import subprocess
from pathlib import Path

import frontmatter

REPO = Path(__file__).parent.parent
SCRIPT = REPO / "scripts" / "build_stock_kb.py"
FIXT_UP = REPO / "tests" / "fixtures" / "mock_upstream"
FIXT_OV = REPO / "tests" / "fixtures" / "mock_overlay"


def test_build_merges_and_tags(tmp_path):
    # Stage independent copies so the test is hermetic.
    up = tmp_path / "upstream"
    ov = tmp_path / "overlay"
    out = tmp_path / "stock-kb"
    shutil.copytree(FIXT_UP, up)
    shutil.copytree(FIXT_OV, ov)
    # Overlay needs scripts/ to be available — copy from the real repo.
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
    # Staged as above, but also place a ticker in overlay that clashes with upstream.
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
    # Source still marked upstream
    assert frontmatter.loads(upa).get("source") == "upstream"
```

- [ ] **Step 4: Run the integration tests**

```bash
pytest tests/test_build_integration.py -v
```

Expected: 2 passed. No external shell / binary dependencies — everything runs in-process Python plus the helper subprocesses.

- [ ] **Step 5: Run the full test suite to confirm everything still passes**

```bash
pytest -v
```

Expected: all tests pass (unit + integration).

### Task 10: Write scaffolding files (README, CLAUDE.overlay, .gitignore)

**Files:**
- Create: `~/projects/personal/rwh-overlay/README.md`
- Create: `~/projects/personal/rwh-overlay/CLAUDE.overlay.md`
- Create: `~/projects/personal/rwh-overlay/.gitignore`
- Create: `~/projects/personal/rwh-overlay/overlay-log.md`

- [ ] **Step 1: Write `.gitignore`**

```
# Python
__pycache__/
*.pyc
.venv/

# Test outputs
.pytest_cache/

# Local Claude state
.claude/settings.local.json

# OS
.DS_Store
Thumbs.db
```

(Note: `stock-kb/` lives as a sibling dir, not inside overlay — no entry needed.)

- [ ] **Step 2: Write `README.md`**

```markdown
# rwh-overlay

Personal overlay on top of [kgajjala/rwh](https://github.com/kgajjala/rwh) — Austin's
investment-analysis extensions built on kgajjala's framework.

## What lives here
- `wiki/tickers/` — my own ticker analyses (outside kgajjala's coverage)
- `wiki/opinions/` — third-party observation sources (e.g., Yun Chen WeChat group)
- `raw/analyses/` — raw source material I author (e.g., Chen timeline)
- `scripts/` — build pipeline that merges upstream + overlay into a published tree
- `CLAUDE.overlay.md` — overlay-specific rules layered on top of upstream `CLAUDE.md`

## What does NOT live here
- kgajjala's tickers (BKNG, LLY, WING, ...) — stay in `../rwh/` (read-only mirror)
- Derived files (index.md, watchlist.md, log.md) — regenerated by build script
- The build output `stock-kb/` — untracked, sibling dir

## How to build
```bash
py scripts/build_stock_kb.py
```
Requires: `py`/`python` and `python-frontmatter` installed. No `rsync` or bash shell needed.

## Day-to-day
- Add new ticker: author files under `wiki/tickers/<TICKER>/`, append line to `overlay-log.md`, run build, commit, push.
- Update Chen observations: append to `raw/analyses/chen.md`, refresh `wiki/opinions/chen-yun.md`, build, commit.
- Pull upstream: build script does this automatically (`git pull --ff-only`).

See `docs/superpowers/specs/2026-04-23-rwh-overlay-architecture-design.md` for the full design.
```

- [ ] **Step 3: Write `CLAUDE.overlay.md`**

```markdown
# CLAUDE.overlay.md — Austin's Extensions

**Read this AFTER `../rwh/CLAUDE.md`** (the upstream framework from kgajjala).
This file adds overlay-specific rules that do not apply to the upstream repo.

---

## Where to write
- **Always write new ticker analyses under `rwh-overlay/wiki/tickers/<TICKER>/`**.
  Never write into `../rwh/`. The upstream mirror is read-only — pre-commit
  hook in `../rwh/.git/hooks/pre-commit` will block commits.
- Chinese translations use `.zh.md` suffix (e.g., `overview.zh.md`), with
  structural parity to the English version and a language-switcher header.

## Derived files — do NOT hand-edit
- `../rwh/wiki/index.md`, `watchlist.md`, `log.md` — upstream files; kgajjala owns.
- Combined `stock-kb/wiki/{index,watchlist,log}.md` — auto-generated by build.
- For your own event log, append a single line to `overlay-log.md` in this repo.

## CRITICAL log.md rendering rule
When appending to `overlay-log.md`, do NOT add code-fence characters — the
build script wraps the merged output in one fence. Just append a bare line:

```
LOG 2026-04-23 14:00 ACTION SCOPE — description
```

## Third-party opinion sources
- Live under `wiki/opinions/`.
- Do NOT satisfy the upstream 15-section thesis standard — they are
  idea-generation and sentiment inputs only.
- A ticker named in an opinion page is not promoted to `wiki/tickers/` unless
  I do independent 10-K/10-Q/IR validation per upstream rule #5.

## Build workflow
- After any content change: run `py scripts/build_stock_kb.py` and inspect
  the output under `../stock-kb/` before committing.
- Commit message convention matches kgajjala's: `feat:`, `fix:`, `docs:`, etc.
```

- [ ] **Step 4: Write empty `overlay-log.md`**

```bash
touch overlay-log.md
```

(Populated in Task 12 with the user's local log entries.)

- [ ] **Step 5: First commit — scaffold + pipeline**

```bash
cd ~/projects/personal/rwh-overlay
git add .gitignore README.md CLAUDE.overlay.md overlay-log.md scripts/ tests/ requirements-dev.txt wiki/.gitkeep-files* raw/.gitkeep* docs/.gitkeep*
# Workaround: if the above glob misses files, do:
git add -A
git status
```

Verify `git status` shows the intended files staged and nothing unexpected. Then:

```bash
git commit -m "feat: scaffold overlay repo and build pipeline

- Python-based frontmatter injection, index/watchlist/log generators
- pure-Python orchestrator with "only-add" (skip-if-exists) policy enforcement
- pytest unit + integration tests
- Overlay-specific CLAUDE rules (CLAUDE.overlay.md)"
```

---

## Phase 2: Content Migration

### Task 11: Move overlay ticker dirs and Chen files from rwh working tree

**Files:**
- Move: `rwh/wiki/tickers/{NVTS,OKLO,POET,WOLF}/` → `rwh-overlay/wiki/tickers/`
- Move: `rwh/wiki/opinions/chen-yun.md` → `rwh-overlay/wiki/opinions/`
- Move: `rwh/raw/analyses/chen.md` → `rwh-overlay/raw/analyses/`

- [ ] **Step 1: Verify source files exist**

```bash
cd ~/projects/personal/rwh
ls wiki/tickers/NVTS wiki/tickers/OKLO wiki/tickers/POET wiki/tickers/WOLF
ls wiki/opinions/chen-yun.md raw/analyses/chen.md
```

Expected: all paths listed without errors.

- [ ] **Step 2: Move tickers**

```bash
cd ~/projects/personal
mv rwh/wiki/tickers/NVTS rwh-overlay/wiki/tickers/
mv rwh/wiki/tickers/OKLO rwh-overlay/wiki/tickers/
mv rwh/wiki/tickers/POET rwh-overlay/wiki/tickers/
mv rwh/wiki/tickers/WOLF rwh-overlay/wiki/tickers/
```

- [ ] **Step 3: Move Chen files**

```bash
mv rwh/wiki/opinions rwh-overlay/wiki/   # whole directory
mv rwh/raw/analyses/chen.md rwh-overlay/raw/analyses/
```

- [ ] **Step 4: Verify**

```bash
cd ~/projects/personal/rwh-overlay
find wiki/tickers -maxdepth 1 -type d | sort
ls wiki/opinions raw/analyses
```

Expected:
```
wiki/tickers
wiki/tickers/NVTS
wiki/tickers/OKLO
wiki/tickers/POET
wiki/tickers/WOLF
```
and `chen-yun.md`, `chen.md` present.

### Task 12: Extract user LOG entries into overlay-log.md

**Files:**
- Modify: `~/projects/personal/rwh-overlay/overlay-log.md`

- [ ] **Step 1: Diff upstream log.md to isolate user-authored LOG entries**

```bash
cd ~/projects/personal/rwh
git diff wiki/log.md | grep -E '^\+LOG ' | sed 's/^\+//' > /tmp/user-log-lines.txt
wc -l /tmp/user-log-lines.txt
```

Expected: ~32 lines (from 2026-04-22 22:40 to 2026-04-23 09:19, plus the "FIX log.md" entry).

- [ ] **Step 2: Append to overlay-log.md**

```bash
cat /tmp/user-log-lines.txt >> ~/projects/personal/rwh-overlay/overlay-log.md
```

- [ ] **Step 3: Remove obsolete entries**

The `LOG 2026-04-23 00:20 FIX log.md` entry described adding a code fence
to upstream's log.md. That fix is now handled by `merge_log.py` at build
time; delete the entry from `overlay-log.md`:

```bash
cd ~/projects/personal/rwh-overlay
sed -i '/FIX log.md — Wrapped all LOG entries/d' overlay-log.md
```

Also delete entries that refer to edits of `index.md` / `watchlist.md` /
`opinions/chen-yun.md` — those files are regenerated or moved, and those
LOG entries would describe operations no longer applicable:

```bash
sed -i '/UPDATE index.md —/d; /UPDATE watchlist.md —/d; /UPDATE opinions\/chen-yun.md —/d' overlay-log.md
```

- [ ] **Step 4: Verify overlay-log.md is clean**

```bash
cat ~/projects/personal/rwh-overlay/overlay-log.md
```

Each remaining line should start with `LOG YYYY-MM-DD HH:MM` and describe
either an INGEST, UPDATE of a ticker dir, PRICE check, TRANSLATE, or
CREATE of an overlay-owned file. Confirm no code-fence markers (```), no
stray content.

### Task 13: Restore rwh to pristine upstream state and install pre-commit guard

**Files:**
- Restore: `rwh/wiki/{index,log,watchlist}.md`, `rwh/CLAUDE.md` via `git checkout`
- Create: `rwh/.git/hooks/pre-commit`

- [ ] **Step 1: Verify only intended user-shared-file changes remain**

```bash
cd ~/projects/personal/rwh
git status
```

Expected: modified `wiki/index.md`, `wiki/log.md`, `wiki/watchlist.md`,
`CLAUDE.md`. All user-added ticker dirs and Chen files should already be
gone (moved in Task 11). `.claude/` and `.stignore` are local-only and
stay untracked.

- [ ] **Step 2: Decide what to do with the `CLAUDE.md` edit**

The local modification adds a "CRITICAL rendering rule" block about log.md
code fences. Compare to upstream by reading the current CLAUDE.md content
— if upstream already has this block (confirm via `git log --all -p CLAUDE.md | grep 'CRITICAL rendering rule'`), the diff shown in working tree is
phantom (line-ending noise). If upstream does NOT have it yet, either:
  (a) PR upstream (recommended — it's general-purpose) — defer.
  (b) Embed in `CLAUDE.overlay.md` as a local reminder.

For this migration, discard the local edit (it's already embodied by the
build script's merge_log.py behavior, and the rule is recorded in
CLAUDE.overlay.md Task 10 Step 3).

- [ ] **Step 3: Discard all four shared-file edits**

```bash
git checkout -- wiki/index.md wiki/log.md wiki/watchlist.md CLAUDE.md
```

- [ ] **Step 4: Verify rwh is pristine**

```bash
git status
```

Expected: only untracked files (`.claude/`, `.stignore`) remain. No
modified files. If `M wiki/log.md` still appears due to CRLF/LF
normalization, run `git checkout -- wiki/log.md` once more, and if it
persists, add a local `.gitattributes` (out of scope — flag for later).

- [ ] **Step 5: Install the pre-commit guard hook**

`.git/hooks/pre-commit`:

```bash
#!/usr/bin/env bash
cat >&2 <<'EOF'
❌ ERROR: personal/rwh/ is a read-only upstream mirror of kgajjala/rwh.

   Do NOT commit into this repo. Author your content in:
       ../rwh-overlay/

   See: docs/superpowers/specs/2026-04-23-rwh-overlay-architecture-design.md
   (migrated to rwh-overlay/docs/superpowers/specs/ after Phase 2).

   If you REALLY need to commit (e.g., maintaining a branch to PR back to
   kgajjala), bypass with: git commit --no-verify
EOF
exit 1
```

Install:

```bash
chmod +x .git/hooks/pre-commit
```

- [ ] **Step 6: Sanity-check the guard**

```bash
cd ~/projects/personal/rwh
git commit --allow-empty -m "test" 2>&1 | head -3
```

Expected: the hook message printed + exit code nonzero. Then:

```bash
echo $?
```

Expected: a nonzero exit code.

### Task 14: Move spec and plan into overlay's docs/

**Files:**
- Move: `rwh/docs/superpowers/specs/2026-04-23-rwh-overlay-architecture-design.md` → `rwh-overlay/docs/superpowers/specs/`
- Move: `rwh/docs/superpowers/plans/2026-04-23-rwh-overlay-implementation.md` → `rwh-overlay/docs/superpowers/plans/`
- Delete: `rwh/docs/` (now empty)

- [ ] **Step 1: Move the two documents**

```bash
cd ~/projects/personal
mv rwh/docs/superpowers/specs/2026-04-23-rwh-overlay-architecture-design.md \
   rwh-overlay/docs/superpowers/specs/
mv rwh/docs/superpowers/plans/2026-04-23-rwh-overlay-implementation.md \
   rwh-overlay/docs/superpowers/plans/
```

- [ ] **Step 2: Remove now-empty directories from rwh workdir**

```bash
rmdir rwh/docs/superpowers/specs rwh/docs/superpowers/plans \
      rwh/docs/superpowers rwh/docs
```

- [ ] **Step 3: Verify rwh workdir is clean**

```bash
cd ~/projects/personal/rwh
git status
```

Expected: same output as after Task 13 Step 4. No new untracked dirs.

### Task 15: Commit migration and push overlay to GitHub

**Files:** (already staged from previous tasks)

- [ ] **Step 1: Stage and commit the migrated content**

```bash
cd ~/projects/personal/rwh-overlay
git add wiki/ raw/ overlay-log.md docs/
git status
```

Expected: the 4 tickers (NVTS, OKLO, POET, WOLF), opinions/chen-yun.md,
raw/analyses/chen.md, overlay-log.md, and the two docs are staged.

```bash
git commit -m "feat: migrate personal content from rwh working tree

- 4 self-authored tickers: NVTS, OKLO, POET, WOLF (EN + ZH)
- Chen observation log: wiki/opinions/chen-yun.md + raw/analyses/chen.md
- overlay-log.md with ~30 LOG entries from original migration period
- Architecture spec + implementation plan under docs/superpowers/"
```

- [ ] **Step 2: Push to GitHub**

```bash
git push -u origin main
```

Expected: push succeeds; remote tracking branch set up.

- [ ] **Step 3: Verify on GitHub**

Open `https://github.com/austinxyz/rwh-overlay` in browser. Confirm:
- Two commits present (scaffold + migration)
- `wiki/tickers/` shows NVTS/OKLO/POET/WOLF
- `docs/superpowers/specs/2026-04-23-rwh-overlay-architecture-design.md` renders

---

## Phase 3: Integration and Acceptance

### Task 16: First real `build_stock_kb.py` run against live content

**Files:**
- Create: `~/projects/personal/stock-kb/` (build output; not in any git)

- [ ] **Step 1: Run the build**

```bash
cd ~/projects/personal/rwh-overlay
py scripts/build_stock_kb.py
```

Expected output ends with a success line like:
`✅ Build complete. Total tickers: 13`.

- [ ] **Step 2: Spot-check the output**

```bash
cd ~/projects/personal/stock-kb
ls wiki/tickers/ | sort
```

Expected: BKNG, DASH, LLY, NVTS, OKLO, PG, POET, RKT, SCHW, SHOP, UNH, WING, WOLF (13 total).

```bash
head -10 wiki/tickers/BKNG/overview.md
head -10 wiki/tickers/NVTS/overview.md
head -10 wiki/opinions/chen-yun.md
```

Expected:
- BKNG has `source: upstream` in frontmatter
- NVTS has `source: austin`
- chen-yun.md has `source: austin-observation`

```bash
head -30 wiki/index.md
head -30 wiki/watchlist.md
head -20 wiki/log.md
```

Expected:
- `index.md` has two tables (Upstream + My Tickers)
- `watchlist.md` has rows for all 13 tickers with source labels
- `log.md` is wrapped in a single ``` fence and sorted by timestamp
  (starts with `LOG 2026-04-05`, ends with the latest overlay entry)

- [ ] **Step 3: Re-run and confirm idempotence**

```bash
py scripts/build_stock_kb.py
py scripts/build_stock_kb.py
```

Expected: both runs succeed; second run output identical to first.

### Task 17: Configure Syncthing share for stock-kb → NAS

**Files:** (Syncthing configuration — UI-only)

- [ ] **Step 1: Determine the target NAS path**

Per spec Section 1 / Quartz architecture: stock KB mounts from NAS at
`/volume1/docker/stock/content/wiki`. The parent directory
`/volume1/docker/stock/content/` is the Syncthing target.

- [ ] **Step 2: Back up existing NAS content**

On the NAS (SSH or DSM File Manager):

```bash
ssh admin@nas 'cp -a /volume1/docker/stock/content /volume1/docker/stock/content.backup-2026-04-23'
```

(If this is a fresh setup with no prior stock content, skip.)

- [ ] **Step 3: Create a new Syncthing folder share**

In the Syncthing Web UI on the local Windows machine:
- Add Folder → Folder ID: `stock-kb`
- Folder Path: `C:\Users\lorra\projects\personal\stock-kb`
- Share with: (select the NAS device entry)
- Advanced → Folder Type: Send Only (optional — one-way from local to NAS)
- Save.

On the NAS's Syncthing UI, accept the share with path
`/volume1/docker/stock/content/`.

- [ ] **Step 4: Wait for first sync to complete**

Monitor the Syncthing UI; wait for both sides to show "Up to Date".

- [ ] **Step 5: Verify on NAS**

```bash
ssh admin@nas 'ls /volume1/docker/stock/content/wiki/tickers/ | wc -l'
```

Expected: 13.

### Task 18: Quartz acceptance test

**Files:** (verification only)

- [ ] **Step 1: Restart the Docker container**

SSH or use DSM Docker UI to restart the Quartz container (so the new
volume content is picked up if it was cached):

```bash
ssh admin@nas 'cd /volume1/docker/second-brain && docker compose -f docker-compose.nas.yml restart'
```

- [ ] **Step 2: Open the Quartz site in a browser**

Navigate to the site URL (whatever the existing second-brain deployment
uses). Go to the stock knowledge base page.

- [ ] **Step 3: Verify unified tree**

- [ ] BKNG page loads, frontmatter-rendered badge shows `[Upstream]`.
- [ ] NVTS page loads, badge shows `[Austin]`.
- [ ] `opinions/chen-yun.md` loads, badge shows `[Chen via Austin]`.
- [ ] Both upstream and overlay tickers appear in the same navigation
      tree under `tickers/`.
- [ ] `index.md` shows both groups (Upstream Tickers + My Tickers).
- [ ] `log.md` renders with per-entry formatting (not one blob).
- [ ] Cross-KB wikilinks (e.g., from wealth → stock) still work.

> **If no badge is rendered**: the `source` frontmatter is on every page,
> but the Quartz layout template may not yet display it. This is listed
> as "Open Question" in the spec — out of scope for this plan. File a
> follow-up to extend `quartz.layout.ts` with a source-badge slot.

- [ ] **Step 4: Test upstream pull cycle**

```bash
cd ~/projects/personal/rwh-overlay
py scripts/build_stock_kb.py
```

The `git pull --ff-only` step will report "Already up to date" (or pull
new commits if any). The build should succeed and produce identical or
updated output. Syncthing should reflect within ~1 minute.

---

## Self-Review

Reviewed against the spec's Section 11 success criteria:

- [x] SC1: `personal/rwh/` has no uncommitted changes — Task 13 Step 3-4
- [x] SC2: `austinxyz/rwh-overlay` exists with pushed content — Task 15
- [x] SC3: `py scripts/build_stock_kb.py` runs cleanly in <10s — Task 16 (no timing assertion, but idempotence check covers correctness)
- [x] SC4: Quartz shows all 13 tickers in unified tree — Task 18
- [x] SC5: Each page has correct `source` frontmatter — Task 16 Step 2 spot-check + Task 18
- [x] SC6: Upstream pull → build → Quartz reflects change — Task 18 Step 4

Placeholder scan: no TBD/TODO/generic "implement later" in the plan. All code blocks have full implementations or concrete commands.

Type/name consistency:
- `inject_frontmatter.py --source {upstream,austin,austin-observation}` used consistently in Tasks 4, 8, 9.
- `gen_index.py`, `gen_watchlist.py`, `merge_log.py` argument names (`--wiki-root`, `--output`, `--upstream`, `--overlay`) consistent across tasks.
- Env vars `RWH_DIR`, `OVERLAY_DIR`, `OUTPUT_DIR`, `SKIP_PULL` consistent in Tasks 8, 9, 16.
- `overlay-log.md` (single-fence-less input) consistent with `merge_log.py` contract and CLAUDE.overlay.md's "CRITICAL log.md rendering rule".

One gap addressed inline: the "CRITICAL rendering rule" migration decision
(Task 13 Step 2) was ambiguous; spec doesn't require preserving the
user's CLAUDE.md edit — resolved by embedding it in CLAUDE.overlay.md
(already done in Task 10 Step 3).
