# `/morning-check` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 `/morning-check` 命令，桥接 EOD 计划和开盘执行决策；建立 `data/positions.md` 持仓追踪机制。

**Architecture:** Python 助手脚本 `scripts/positions.py` 提供持仓 CRUD 接口（读写 markdown 表格），`.claude/commands/morning-check.md` 命令编排实时数据拉取 + 决策矩阵 + 持仓更新。所有持仓数据本地化（gitignored）。

**Tech Stack:** Python 3, pytest, yfinance（已有）, markdown table parsing（无外部依赖，简单 line-based parser）

**Spec:** `docs/superpowers/specs/2026-04-28-morning-check-design.md`

---

## File Structure

| 文件 | 角色 |
|------|------|
| `scripts/positions.py` | 持仓 CRUD 助手（read/list/add/update/close）+ CLI argparse 接口 |
| `tests/test_positions.py` | positions.py 单元测试 |
| `.claude/commands/morning-check.md` | 命令编排（调用 positions.py + yfinance + 决策矩阵）|
| `data/positions.md` | 持仓数据（运行时生成，gitignored）|
| `data/.gitkeep` | 保持 data/ 目录存在 |
| `.gitignore` | 新增 `data/positions.md` |
| `README.md` | 新增 `/morning-check` 到命令表 |

---

## Task 1: 项目骨架（目录、.gitignore、空类型）

**Files:**
- Create: `data/.gitkeep` (空文件)
- Create: `scripts/positions.py`
- Create: `tests/test_positions.py`
- Modify: `.gitignore`

- [ ] **Step 1: 创建 data 目录和 .gitkeep**

```bash
mkdir -p data && touch data/.gitkeep
```

- [ ] **Step 2: 更新 .gitignore**

在 `.gitignore` 末尾追加：

```
# Local position tracking (sensitive)
data/positions.md
```

- [ ] **Step 3: 写 positions.py 骨架**

```python
#!/usr/bin/env python3
"""Position tracker for /morning-check command.

Reads/writes `data/positions.md` with two markdown tables:
- Active Positions
- Closed Positions
"""
from __future__ import annotations
import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

# Force UTF-8 output (Windows cp1252 fix)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
POSITIONS_FILE = REPO_ROOT / "data" / "positions.md"


@dataclass
class Position:
    ticker: str
    shares: int
    avg_cost: float
    entry_date: str
    stop: float | None = None
    target1: float | None = None
    target2: float | None = None
    status: str = "Active"
    notes: str = ""


@dataclass
class ClosedPosition:
    ticker: str
    shares: int
    entry_date: str
    exit_date: str
    avg_cost: float
    avg_exit: float
    pnl_dollar: float
    pnl_pct: float
    reason: str
    closed_date: str


if __name__ == "__main__":
    print("positions.py — see --help")
```

- [ ] **Step 4: 写测试骨架**

```python
"""Tests for scripts/positions.py."""
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import positions


def test_imports_ok():
    """Smoke test — module imports cleanly."""
    assert positions.Position is not None
    assert positions.ClosedPosition is not None
```

- [ ] **Step 5: 运行测试**

```bash
.venv/Scripts/python.exe -m pytest tests/test_positions.py -v
```
Expected: PASS (1 test)

- [ ] **Step 6: 提交**

```bash
git add data/.gitkeep scripts/positions.py tests/test_positions.py .gitignore
git commit -m "feat: positions.py skeleton with Position/ClosedPosition types"
```

---

## Task 2: 实现 add() — 创建文件 + 写新仓

**Files:**
- Modify: `scripts/positions.py`
- Modify: `tests/test_positions.py`

- [ ] **Step 1: 写测试**

在 `tests/test_positions.py` 末尾追加：

```python
import tempfile
import shutil

def test_add_creates_file_when_missing(monkeypatch):
    """add() creates positions.md with template if file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_file = Path(tmp) / "positions.md"
        monkeypatch.setattr(positions, "POSITIONS_FILE", fake_file)

        pos = positions.Position(
            ticker="POET", shares=500, avg_cost=11.20, entry_date="2026-04-15",
            stop=9.50, target1=14.00, target2=18.00, status="Active",
            notes="Test entry"
        )
        positions.add(pos)

        assert fake_file.exists()
        content = fake_file.read_text(encoding="utf-8")
        assert "# Active Positions" in content
        assert "# Closed Positions" in content
        assert "POET" in content
        assert "500" in content
        assert "11.20" in content


def test_add_appends_to_existing_file(monkeypatch):
    """add() appends new row to existing Active table."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_file = Path(tmp) / "positions.md"
        monkeypatch.setattr(positions, "POSITIONS_FILE", fake_file)

        pos1 = positions.Position(ticker="POET", shares=500, avg_cost=11.20,
                                   entry_date="2026-04-15", status="Active")
        pos2 = positions.Position(ticker="INTT", shares=200, avg_cost=14.50,
                                   entry_date="2026-04-10", status="Active")
        positions.add(pos1)
        positions.add(pos2)

        content = fake_file.read_text(encoding="utf-8")
        assert "POET" in content
        assert "INTT" in content
```

- [ ] **Step 2: 运行测试 — 应失败**

```bash
.venv/Scripts/python.exe -m pytest tests/test_positions.py -v
```
Expected: FAIL with "module 'positions' has no attribute 'add'"

- [ ] **Step 3: 实现 add() + 模板**

在 `scripts/positions.py` 中（在 `if __name__` 之前）添加：

```python
TEMPLATE = """# Active Positions

> Last updated: {date}
> Maintained by `/morning-check`. Manual edits OK.

| Ticker | Shares | Avg Cost | Entry Date | Stop | Target 1 | Target 2 | Status | Notes |
|--------|--------|----------|------------|------|----------|----------|--------|-------|

# Closed Positions

| Ticker | Shares | Entry | Exit | Avg Cost | Avg Exit | P&L $ | P&L % | Reason | Closed Date |
|--------|--------|-------|------|----------|----------|-------|-------|--------|-------------|
"""


def _fmt_optional_dollar(value: float | None) -> str:
    return f"${value:.2f}" if value is not None else ""


def _format_active_row(pos: Position) -> str:
    return (
        f"| {pos.ticker} | {pos.shares} | ${pos.avg_cost:.2f} | {pos.entry_date} | "
        f"{_fmt_optional_dollar(pos.stop)} | {_fmt_optional_dollar(pos.target1)} | "
        f"{_fmt_optional_dollar(pos.target2)} | {pos.status} | {pos.notes} |"
    )


def _ensure_file_exists() -> None:
    if not POSITIONS_FILE.exists():
        from datetime import date
        POSITIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        POSITIONS_FILE.write_text(
            TEMPLATE.format(date=date.today().isoformat()),
            encoding="utf-8",
        )


def add(pos: Position) -> None:
    """Append a new position row to the Active table."""
    _ensure_file_exists()
    content = POSITIONS_FILE.read_text(encoding="utf-8")

    # Insert new row before the "# Closed Positions" section
    closed_marker = "# Closed Positions"
    idx = content.find(closed_marker)
    if idx == -1:
        raise ValueError("positions.md missing '# Closed Positions' section")

    # Find end of Active table separator line and insert after it
    active_section = content[:idx]
    new_row = _format_active_row(pos) + "\n"
    new_content = active_section.rstrip() + "\n" + new_row + "\n" + content[idx:]
    POSITIONS_FILE.write_text(new_content, encoding="utf-8")
```

- [ ] **Step 4: 运行测试 — 应通过**

```bash
.venv/Scripts/python.exe -m pytest tests/test_positions.py -v
```
Expected: PASS (3 tests)

- [ ] **Step 5: 提交**

```bash
git add scripts/positions.py tests/test_positions.py
git commit -m "feat: positions.add() creates file and appends new row"
```

---

## Task 3: 实现 read() — 单 ticker 查询

**Files:**
- Modify: `scripts/positions.py`
- Modify: `tests/test_positions.py`

- [ ] **Step 1: 写测试**

```python
def test_read_returns_position(monkeypatch):
    """read() returns matching Position dataclass for active ticker."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_file = Path(tmp) / "positions.md"
        monkeypatch.setattr(positions, "POSITIONS_FILE", fake_file)

        pos = positions.Position(
            ticker="POET", shares=500, avg_cost=11.20, entry_date="2026-04-15",
            stop=9.50, target1=14.00, target2=18.00, status="Active",
            notes="Test"
        )
        positions.add(pos)

        result = positions.read("POET")
        assert result is not None
        assert result.ticker == "POET"
        assert result.shares == 500
        assert result.avg_cost == 11.20
        assert result.stop == 9.50
        assert result.target1 == 14.00
        assert result.status == "Active"


def test_read_returns_none_for_missing_ticker(monkeypatch):
    """read() returns None when ticker not found."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_file = Path(tmp) / "positions.md"
        monkeypatch.setattr(positions, "POSITIONS_FILE", fake_file)
        positions._ensure_file_exists()

        assert positions.read("NOTHERE") is None


def test_read_returns_none_when_file_missing(monkeypatch):
    """read() returns None gracefully when positions.md doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_file = Path(tmp) / "positions.md"
        monkeypatch.setattr(positions, "POSITIONS_FILE", fake_file)

        assert positions.read("POET") is None
```

- [ ] **Step 2: 运行测试 — 应失败**

Expected: FAIL with "module 'positions' has no attribute 'read'"

- [ ] **Step 3: 实现 read() + 表格 parser**

在 `scripts/positions.py` 中（add() 之后）添加：

```python
def _parse_dollar(s: str) -> float | None:
    s = s.strip()
    if not s:
        return None
    return float(s.replace("$", "").replace(",", ""))


def _parse_active_row(line: str) -> Position | None:
    """Parse a single | A | B | C | ... | row into a Position. None if invalid."""
    parts = [p.strip() for p in line.split("|")]
    # Markdown rows have leading/trailing empty parts due to | at edges
    # Filter and check we have exactly 9 fields
    cells = [p for p in parts if p != ""]
    if len(cells) < 4:  # at minimum need ticker/shares/cost/date
        return None
    # Skip header/separator rows
    if cells[0].lower() == "ticker" or "---" in cells[0]:
        return None
    try:
        return Position(
            ticker=cells[0],
            shares=int(cells[1]),
            avg_cost=_parse_dollar(cells[2]),
            entry_date=cells[3],
            stop=_parse_dollar(cells[4]) if len(cells) > 4 else None,
            target1=_parse_dollar(cells[5]) if len(cells) > 5 else None,
            target2=_parse_dollar(cells[6]) if len(cells) > 6 else None,
            status=cells[7] if len(cells) > 7 else "Active",
            notes=cells[8] if len(cells) > 8 else "",
        )
    except (ValueError, IndexError):
        return None


def _iter_active_rows() -> list[Position]:
    """Read all active position rows from positions.md."""
    if not POSITIONS_FILE.exists():
        return []
    content = POSITIONS_FILE.read_text(encoding="utf-8")
    closed_marker = "# Closed Positions"
    idx = content.find(closed_marker)
    active_section = content[:idx] if idx != -1 else content

    rows = []
    for line in active_section.splitlines():
        if not line.startswith("|"):
            continue
        pos = _parse_active_row(line)
        if pos is not None:
            rows.append(pos)
    return rows


def read(ticker: str) -> Position | None:
    """Return Position for a single active ticker, or None if not found."""
    ticker = ticker.upper()
    for pos in _iter_active_rows():
        if pos.ticker.upper() == ticker:
            return pos
    return None
```

- [ ] **Step 4: 运行测试 — 应通过**

Expected: PASS (6 tests)

- [ ] **Step 5: 提交**

```bash
git add scripts/positions.py tests/test_positions.py
git commit -m "feat: positions.read() with markdown table parser"
```

---

## Task 4: 实现 list_active()

**Files:**
- Modify: `scripts/positions.py`
- Modify: `tests/test_positions.py`

- [ ] **Step 1: 写测试**

```python
def test_list_active_returns_all_active(monkeypatch):
    """list_active() returns all rows with status=Active."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_file = Path(tmp) / "positions.md"
        monkeypatch.setattr(positions, "POSITIONS_FILE", fake_file)

        positions.add(positions.Position(ticker="POET", shares=500, avg_cost=11.20,
                                          entry_date="2026-04-15", status="Active"))
        positions.add(positions.Position(ticker="INTT", shares=200, avg_cost=14.50,
                                          entry_date="2026-04-10", status="Active"))
        positions.add(positions.Position(ticker="WOLF", shares=100, avg_cost=25.00,
                                          entry_date="2026-03-15", status="Watching"))

        active = positions.list_active()
        tickers = [p.ticker for p in active]
        assert "POET" in tickers
        assert "INTT" in tickers
        assert "WOLF" not in tickers  # status=Watching, not Active
        assert len(active) == 2


def test_list_active_empty_when_file_missing(monkeypatch):
    """list_active() returns [] when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_file = Path(tmp) / "positions.md"
        monkeypatch.setattr(positions, "POSITIONS_FILE", fake_file)

        assert positions.list_active() == []
```

- [ ] **Step 2: 运行测试 — 应失败**

Expected: FAIL with "no attribute 'list_active'"

- [ ] **Step 3: 实现 list_active()**

```python
def list_active() -> list[Position]:
    """Return all positions with Active or Trimmed status."""
    return [p for p in _iter_active_rows() if p.status in ("Active", "Trimmed")]
```

- [ ] **Step 4: 运行测试 — 应通过**

Expected: PASS (8 tests)

- [ ] **Step 5: 提交**

```bash
git add scripts/positions.py tests/test_positions.py
git commit -m "feat: positions.list_active() filters by status"
```

---

## Task 5: 实现 update()

**Files:**
- Modify: `scripts/positions.py`
- Modify: `tests/test_positions.py`

- [ ] **Step 1: 写测试**

```python
def test_update_modifies_single_field(monkeypatch):
    """update() changes specified field while preserving others."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_file = Path(tmp) / "positions.md"
        monkeypatch.setattr(positions, "POSITIONS_FILE", fake_file)

        positions.add(positions.Position(ticker="POET", shares=500, avg_cost=11.20,
                                          entry_date="2026-04-15", stop=9.50,
                                          status="Active", notes="Original"))

        positions.update("POET", stop=10.50, notes="Stop tightened")

        result = positions.read("POET")
        assert result.stop == 10.50
        assert result.notes == "Stop tightened"
        assert result.shares == 500  # Preserved
        assert result.avg_cost == 11.20  # Preserved


def test_update_changes_status_to_trimmed(monkeypatch):
    """update() can change shares + status for partial trim."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_file = Path(tmp) / "positions.md"
        monkeypatch.setattr(positions, "POSITIONS_FILE", fake_file)

        positions.add(positions.Position(ticker="POET", shares=500, avg_cost=11.20,
                                          entry_date="2026-04-15", status="Active"))

        positions.update("POET", shares=250, status="Trimmed",
                         notes="Trimmed 50% on 4/28")

        result = positions.read("POET")
        assert result.shares == 250
        assert result.status == "Trimmed"


def test_update_raises_for_missing_ticker(monkeypatch):
    """update() raises KeyError when ticker not in active positions."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_file = Path(tmp) / "positions.md"
        monkeypatch.setattr(positions, "POSITIONS_FILE", fake_file)
        positions._ensure_file_exists()

        try:
            positions.update("NOTHERE", stop=5.00)
            assert False, "Should have raised KeyError"
        except KeyError as e:
            assert "NOTHERE" in str(e)
```

- [ ] **Step 2: 运行测试 — 应失败**

Expected: FAIL with "no attribute 'update'"

- [ ] **Step 3: 实现 update()**

```python
def update(ticker: str, **fields) -> None:
    """Update specified fields on an existing active position.

    Allowed fields: shares, avg_cost, stop, target1, target2, status, notes
    """
    ticker = ticker.upper()
    allowed = {"shares", "avg_cost", "stop", "target1", "target2", "status", "notes"}
    bad = set(fields) - allowed
    if bad:
        raise ValueError(f"Unknown fields: {bad}")

    if not POSITIONS_FILE.exists():
        raise KeyError(f"positions.md does not exist; ticker {ticker} not found")

    content = POSITIONS_FILE.read_text(encoding="utf-8")
    lines = content.splitlines()
    found = False

    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        pos = _parse_active_row(line)
        if pos is None:
            continue
        if pos.ticker.upper() == ticker:
            for key, val in fields.items():
                setattr(pos, key, val)
            lines[i] = _format_active_row(pos)
            found = True
            break

    if not found:
        raise KeyError(f"Ticker {ticker} not found in active positions")

    POSITIONS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
```

- [ ] **Step 4: 运行测试 — 应通过**

Expected: PASS (11 tests)

- [ ] **Step 5: 提交**

```bash
git add scripts/positions.py tests/test_positions.py
git commit -m "feat: positions.update() modifies fields in-place"
```

---

## Task 6: 实现 close() — 移到 Closed Positions

**Files:**
- Modify: `scripts/positions.py`
- Modify: `tests/test_positions.py`

- [ ] **Step 1: 写测试**

```python
def test_close_moves_position_to_closed(monkeypatch):
    """close() removes from Active and appends to Closed Positions."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_file = Path(tmp) / "positions.md"
        monkeypatch.setattr(positions, "POSITIONS_FILE", fake_file)

        positions.add(positions.Position(ticker="POET", shares=500, avg_cost=11.20,
                                          entry_date="2026-04-15", status="Active"))

        positions.close("POET", avg_exit=7.95, reason="Stop broken",
                        closed_date="2026-04-28")

        # No longer in active
        assert positions.read("POET") is None

        # Verify Closed Positions row exists
        content = fake_file.read_text(encoding="utf-8")
        closed_section = content.split("# Closed Positions")[1]
        assert "POET" in closed_section
        assert "$7.95" in closed_section or "7.95" in closed_section
        assert "Stop broken" in closed_section
        # P&L = (7.95 - 11.20) * 500 = -1625
        assert "-$1625" in closed_section or "-1625" in closed_section


def test_close_computes_pnl_correctly(monkeypatch):
    """close() correctly computes P&L $ and P&L %."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_file = Path(tmp) / "positions.md"
        monkeypatch.setattr(positions, "POSITIONS_FILE", fake_file)

        positions.add(positions.Position(ticker="WOLF", shares=200, avg_cost=25.50,
                                          entry_date="2026-03-15", status="Active"))

        positions.close("WOLF", avg_exit=32.00, reason="Target 1 hit",
                        closed_date="2026-04-20")

        content = fake_file.read_text(encoding="utf-8")
        # P&L $ = (32 - 25.5) * 200 = 1300
        # P&L % = (32/25.5 - 1) * 100 = 25.49%
        assert "$1300" in content or "1300" in content
        assert "+25.5%" in content or "25.5%" in content
```

- [ ] **Step 2: 运行测试 — 应失败**

Expected: FAIL with "no attribute 'close'"

- [ ] **Step 3: 实现 close()**

```python
def _format_closed_row(c: ClosedPosition) -> str:
    pnl_sign = "+" if c.pnl_dollar >= 0 else ""
    pct_sign = "+" if c.pnl_pct >= 0 else ""
    return (
        f"| {c.ticker} | {c.shares} | {c.entry_date} | {c.exit_date} | "
        f"${c.avg_cost:.2f} | ${c.avg_exit:.2f} | "
        f"{pnl_sign}${c.pnl_dollar:.0f} | {pct_sign}{c.pnl_pct:.1f}% | "
        f"{c.reason} | {c.closed_date} |"
    )


def close(ticker: str, avg_exit: float, reason: str, closed_date: str) -> None:
    """Move an active position to Closed Positions with computed P&L."""
    ticker = ticker.upper()
    pos = read(ticker)
    if pos is None:
        raise KeyError(f"Ticker {ticker} not found in active positions")

    pnl_dollar = (avg_exit - pos.avg_cost) * pos.shares
    pnl_pct = (avg_exit / pos.avg_cost - 1) * 100

    closed = ClosedPosition(
        ticker=pos.ticker,
        shares=pos.shares,
        entry_date=pos.entry_date,
        exit_date=closed_date,
        avg_cost=pos.avg_cost,
        avg_exit=avg_exit,
        pnl_dollar=pnl_dollar,
        pnl_pct=pnl_pct,
        reason=reason,
        closed_date=closed_date,
    )

    # Remove from active table
    content = POSITIONS_FILE.read_text(encoding="utf-8")
    lines = content.splitlines()
    new_lines = []
    for line in lines:
        if not line.startswith("|"):
            new_lines.append(line)
            continue
        pos_check = _parse_active_row(line)
        if pos_check and pos_check.ticker.upper() == ticker:
            continue  # skip this row (it's the one being closed)
        new_lines.append(line)

    # Append to Closed Positions table
    new_content = "\n".join(new_lines)
    if not new_content.endswith("\n"):
        new_content += "\n"
    new_content += _format_closed_row(closed) + "\n"
    POSITIONS_FILE.write_text(new_content, encoding="utf-8")
```

- [ ] **Step 4: 运行测试 — 应通过**

Expected: PASS (13 tests)

- [ ] **Step 5: 提交**

```bash
git add scripts/positions.py tests/test_positions.py
git commit -m "feat: positions.close() moves to Closed with computed P&L"
```

---

## Task 7: CLI argparse 接口

**Files:**
- Modify: `scripts/positions.py`
- Modify: `tests/test_positions.py`

- [ ] **Step 1: 写 CLI 测试**

```python
import subprocess


def test_cli_read_returns_json(monkeypatch, tmp_path):
    """CLI read returns JSON to stdout."""
    fake_file = tmp_path / "positions.md"

    # Pre-populate
    monkeypatch.setattr(positions, "POSITIONS_FILE", fake_file)
    positions.add(positions.Position(ticker="POET", shares=500, avg_cost=11.20,
                                      entry_date="2026-04-15", status="Active"))

    # Run CLI subprocess
    script = REPO_ROOT / "scripts" / "positions.py"
    import os
    result = subprocess.run(
        [sys.executable, str(script), "read", "--ticker", "POET"],
        env={**os.environ, "POSITIONS_FILE": str(fake_file)},
        capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ticker"] == "POET"
    assert data["shares"] == 500


def test_cli_read_missing_returns_null(tmp_path):
    """CLI read prints 'null' for missing ticker."""
    fake_file = tmp_path / "positions.md"
    fake_file.write_text(positions.TEMPLATE.format(date="2026-04-28"), encoding="utf-8")

    script = REPO_ROOT / "scripts" / "positions.py"
    import os
    result = subprocess.run(
        [sys.executable, str(script), "read", "--ticker", "NOTHERE"],
        env={**os.environ, "POSITIONS_FILE": str(fake_file)},
        capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "null"
```

- [ ] **Step 2: 运行测试 — 应失败（CLI 还没实现）**

Expected: FAIL（CLI not implemented）

- [ ] **Step 3: 实现 CLI dispatch**

替换 `scripts/positions.py` 末尾的 `if __name__ == "__main__":` 块为：

```python
def _resolve_positions_file() -> None:
    """Allow override via env var POSITIONS_FILE (used in tests)."""
    import os
    global POSITIONS_FILE
    env_path = os.environ.get("POSITIONS_FILE")
    if env_path:
        POSITIONS_FILE = Path(env_path)


def _cmd_read(args) -> None:
    pos = read(args.ticker)
    print(json.dumps(asdict(pos)) if pos else "null")


def _cmd_list(args) -> None:
    positions_list = list_active()
    if args.status:
        positions_list = [p for p in positions_list if p.status == args.status]
    print(json.dumps([asdict(p) for p in positions_list], indent=2))


def _cmd_add(args) -> None:
    pos = Position(
        ticker=args.ticker.upper(), shares=args.shares, avg_cost=args.avg_cost,
        entry_date=args.entry_date, stop=args.stop,
        target1=args.target1, target2=args.target2,
        status=args.status, notes=args.notes or "",
    )
    add(pos)
    print(json.dumps({"ok": True, "added": asdict(pos)}))


def _cmd_update(args) -> None:
    fields = {k: v for k, v in vars(args).items()
              if k in {"shares", "avg_cost", "stop", "target1", "target2", "status", "notes"}
              and v is not None}
    update(args.ticker, **fields)
    print(json.dumps({"ok": True, "ticker": args.ticker.upper(), "updated": fields}))


def _cmd_close(args) -> None:
    close(args.ticker, args.avg_exit, args.reason, args.closed_date)
    print(json.dumps({"ok": True, "ticker": args.ticker.upper(), "closed": True}))


def main() -> None:
    _resolve_positions_file()
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_read = sub.add_parser("read", help="Read single ticker position")
    p_read.add_argument("--ticker", required=True)
    p_read.set_defaults(func=_cmd_read)

    p_list = sub.add_parser("list", help="List active positions")
    p_list.add_argument("--status", help="Filter by status (Active/Trimmed/Watching)")
    p_list.set_defaults(func=_cmd_list)

    p_add = sub.add_parser("add", help="Add new position")
    p_add.add_argument("--ticker", required=True)
    p_add.add_argument("--shares", type=int, required=True)
    p_add.add_argument("--avg-cost", type=float, required=True, dest="avg_cost")
    p_add.add_argument("--entry-date", required=True, dest="entry_date")
    p_add.add_argument("--stop", type=float)
    p_add.add_argument("--target1", type=float)
    p_add.add_argument("--target2", type=float)
    p_add.add_argument("--status", default="Active")
    p_add.add_argument("--notes", default="")
    p_add.set_defaults(func=_cmd_add)

    p_upd = sub.add_parser("update", help="Update active position fields")
    p_upd.add_argument("--ticker", required=True)
    p_upd.add_argument("--shares", type=int)
    p_upd.add_argument("--avg-cost", type=float, dest="avg_cost")
    p_upd.add_argument("--stop", type=float)
    p_upd.add_argument("--target1", type=float)
    p_upd.add_argument("--target2", type=float)
    p_upd.add_argument("--status")
    p_upd.add_argument("--notes")
    p_upd.set_defaults(func=_cmd_update)

    p_cls = sub.add_parser("close", help="Close active position")
    p_cls.add_argument("--ticker", required=True)
    p_cls.add_argument("--avg-exit", type=float, required=True, dest="avg_exit")
    p_cls.add_argument("--reason", required=True)
    p_cls.add_argument("--closed-date", required=True, dest="closed_date")
    p_cls.set_defaults(func=_cmd_close)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试 — 应通过**

Expected: PASS (15 tests)

- [ ] **Step 5: 手动验证 CLI**

```bash
.venv/Scripts/python.exe scripts/positions.py --help
.venv/Scripts/python.exe scripts/positions.py read --ticker POET
```
Expected: 第一个显示帮助；第二个输出 `null`（因为真实文件没数据）

- [ ] **Step 6: 提交**

```bash
git add scripts/positions.py tests/test_positions.py
git commit -m "feat: positions.py CLI dispatch (read/list/add/update/close)"
```

---

## Task 8: 创建 morning-check.md 命令（单 ticker 模式）

**Files:**
- Create: `.claude/commands/morning-check.md`

- [ ] **Step 1: 写命令文件**

完整命令文件内容见上方 Task 8 的 Step 1（包含 8 步流程：normalize、检测持仓、检测昨日计划、拉实时数据、应用决策矩阵、输出报告、用户确认、更新 positions.md）。

- [ ] **Step 2: 手动 smoke test**

实际调用：

```
/morning-check INTT
```

Expected: 命令读取 INTT 持仓状态（无）→ 检查 wiki/tickers/INTT/entry-*.md（可能也无）→ 进入生成模式 → 拉实时数据 → 输出决策报告。

- [ ] **Step 3: 提交**

```bash
git add .claude/commands/morning-check.md
git commit -m "feat: /morning-check command (single ticker deep mode)"
```

---

## Task 9: 添加 ALL 模式到 morning-check.md

**Files:**
- Modify: `.claude/commands/morning-check.md`

- [ ] **Step 1: 在 morning-check.md Step 1 后插入 ALL 模式分支**

ALL 模式：读 positions.list_active() → 对每只 ticker 跑简化版决策（不询问 fills、不更新文件）→ 输出简表 + 行动摘要。

- [ ] **Step 2: 手动 smoke test ALL 模式**

```
/morning-check ALL
```

如果 positions.md 为空，应输出"无持仓，无可扫描"。否则按表格输出。

- [ ] **Step 3: 提交**

```bash
git add .claude/commands/morning-check.md
git commit -m "feat: /morning-check ALL batch scan mode"
```

---

## Task 10: README 更新 + 集成测试

**Files:**
- Modify: `README.md`
- Modify: `docs/requirements.md`（如存在并需要保持同步）

- [ ] **Step 1: 更新 README.md 命令表**

在 Slash Commands 表格中插入：

```markdown
| `/morning-check <TICKER>` | Open-time decision: compare live price to entry plan, output Buy/Wait/Skip/Trim/Exit recommendation |
| `/morning-check ALL` | Batch scan all active positions (from `data/positions.md`) |
```

Day-to-day 部分加入：

```markdown
- Morning open: `/morning-check <TICKER>` (single deep) or `/morning-check ALL` (batch positions scan).
- Position tracking: `data/positions.md` (gitignored, maintained by `/morning-check`).
```

- [ ] **Step 2: 更新 docs/requirements.md（如需要）**

如该文件存在 Claude 命令列表区段，加入相应条目。

- [ ] **Step 3: 运行完整测试套件**

```bash
.venv/Scripts/python.exe -m pytest tests/test_positions.py -v
```

Expected: 所有测试通过（应有 15 个）。

- [ ] **Step 4: 端到端验证**

```bash
# 1. 添加测试持仓
.venv/Scripts/python.exe scripts/positions.py add \
  --ticker POET --shares 500 --avg-cost 11.20 --entry-date 2026-04-15 \
  --stop 9.50 --target1 14.00 --notes "Integration test"

# 2. 读取
.venv/Scripts/python.exe scripts/positions.py read --ticker POET

# 3. 列出
.venv/Scripts/python.exe scripts/positions.py list --status Active

# 4. 调整止损
.venv/Scripts/python.exe scripts/positions.py update --ticker POET --stop 8.50

# 5. 平仓
.venv/Scripts/python.exe scripts/positions.py close \
  --ticker POET --avg-exit 7.95 --reason "Stop broken" --closed-date 2026-04-28

# 6. 确认 data/positions.md 内容正确，然后清理
rm data/positions.md
```

- [ ] **Step 5: 提交**

```bash
git add README.md docs/requirements.md
git commit -m "docs: document /morning-check command in README"
```
