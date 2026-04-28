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
