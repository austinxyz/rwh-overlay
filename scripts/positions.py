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
