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


def _parse_dollar(s: str) -> float | None:
    """Parse dollar string like '$11.20' or empty string to float."""
    s = s.strip()
    if not s:
        return None
    return float(s.replace("$", "").replace(",", ""))


def _parse_active_row(line: str) -> Position | None:
    """Parse a single | A | B | C | ... | row into a Position. None if invalid."""
    parts = [p.strip() for p in line.split("|")]
    cells = [p for p in parts if p != ""]
    if len(cells) < 4:
        return None
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


def list_active() -> list[Position]:
    """Return all positions with Active or Trimmed status."""
    return [p for p in _iter_active_rows() if p.status in ("Active", "Trimmed")]


if __name__ == "__main__":
    print("positions.py — see --help")
