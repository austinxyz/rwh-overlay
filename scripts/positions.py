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
    shares: float  # supports fractional shares (e.g. 75.587)
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
    shares: float  # supports fractional shares
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


def _fmt_shares(value: float) -> str:
    """Format share count: int if whole, otherwise up to 4 decimals trimmed."""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _format_active_row(pos: Position) -> str:
    return (
        f"| {pos.ticker} | {_fmt_shares(pos.shares)} | ${pos.avg_cost:.2f} | {pos.entry_date} | "
        f"{_fmt_optional_dollar(pos.stop)} | {_fmt_optional_dollar(pos.target1)} | "
        f"{_fmt_optional_dollar(pos.target2)} | {pos.status} | {pos.notes} |"
    )


def _format_closed_row(c: ClosedPosition) -> str:
    """Format a closed position as a markdown table row."""
    pnl_sign = "+" if c.pnl_dollar >= 0 else ""
    pct_sign = "+" if c.pnl_pct >= 0 else ""
    return (
        f"| {c.ticker} | {_fmt_shares(c.shares)} | {c.entry_date} | {c.exit_date} | "
        f"${c.avg_cost:.2f} | ${c.avg_exit:.2f} | "
        f"{pnl_sign}${c.pnl_dollar:.0f} | {pct_sign}{c.pnl_pct:.1f}% | "
        f"{c.reason} | {c.closed_date} |"
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
    """Parse a single | A | B | C | ... | row into a Position. None if invalid.

    Preserves empty cells (for None stop/target/notes round-tripping). Only
    strips the leading/trailing empties caused by `|` at line edges.
    """
    cells = [p.strip() for p in line.split("|")]
    # Drop leading/trailing empties from | at line edges (do not filter internals)
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    if len(cells) < 4:
        return None
    if cells[0].lower() == "ticker" or "---" in cells[0]:
        return None
    try:
        return Position(
            ticker=cells[0],
            shares=float(cells[1]),
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

    # Split into active + closed sections so we only remove from active
    content = POSITIONS_FILE.read_text(encoding="utf-8")
    closed_marker = "# Closed Positions"
    idx = content.find(closed_marker)
    if idx == -1:
        raise ValueError("positions.md missing '# Closed Positions' section")

    active_part = content[:idx]
    closed_part = content[idx:]

    # Remove the matching row from active_part only
    active_lines = active_part.splitlines()
    new_active_lines = []
    for line in active_lines:
        if line.startswith("|"):
            pos_check = _parse_active_row(line)
            if pos_check and pos_check.ticker.upper() == ticker:
                continue
        new_active_lines.append(line)

    # Append closed row to closed_part
    new_active = "\n".join(new_active_lines).rstrip() + "\n\n"
    new_closed = closed_part.rstrip() + "\n" + _format_closed_row(closed) + "\n"
    POSITIONS_FILE.write_text(new_active + new_closed, encoding="utf-8")


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
    p_add.add_argument("--shares", type=float, required=True)
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
    p_upd.add_argument("--shares", type=float)
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
