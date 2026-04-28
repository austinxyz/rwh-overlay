"""Tests for scripts/positions.py."""
from pathlib import Path
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import positions


def test_imports_ok():
    """Smoke test — module imports cleanly."""
    assert positions.Position is not None
    assert positions.ClosedPosition is not None


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
