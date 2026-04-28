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


def test_list_active_returns_all_active(monkeypatch):
    """list_active() returns all rows with status=Active.

    Uses minimal Position constructor (no optional fields) — also serves as
    regression coverage for empty-cell parsing in _parse_active_row.
    """
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


def test_round_trip_position_with_none_optional_fields(monkeypatch):
    """Regression: position with stop/target/notes=None must round-trip via add+read."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_file = Path(tmp) / "positions.md"
        monkeypatch.setattr(positions, "POSITIONS_FILE", fake_file)

        original = positions.Position(
            ticker="POET", shares=500, avg_cost=11.20, entry_date="2026-04-15",
            status="Active",  # stop, target1, target2 default to None; notes=""
        )
        positions.add(original)

        result = positions.read("POET")
        assert result is not None
        assert result.ticker == "POET"
        assert result.shares == 500
        assert result.avg_cost == 11.20
        assert result.entry_date == "2026-04-15"
        assert result.stop is None
        assert result.target1 is None
        assert result.target2 is None
        assert result.status == "Active"
        assert result.notes == ""


def test_list_active_empty_when_file_missing(monkeypatch):
    """list_active() returns [] when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_file = Path(tmp) / "positions.md"
        monkeypatch.setattr(positions, "POSITIONS_FILE", fake_file)

        assert positions.list_active() == []


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
