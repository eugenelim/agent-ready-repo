"""Resolve the assimilate-repo skill's runtime tree for the tests that exercise it.

Tests live outside the runtime payload (ADR-0071); the modules they exercise
live under `.apm/`. Nothing in this directory is projected into an installed
environment.
"""

from __future__ import annotations

import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "assimilate-repo"
SCRIPTS = SKILL / "scripts"
if not SCRIPTS.is_dir():                      # wrong parents[] depth after a move
    raise SystemExit(f"skill scripts dir not found at {SCRIPTS}")
sys.path.insert(0, str(SCRIPTS))
